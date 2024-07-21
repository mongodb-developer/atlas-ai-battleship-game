import streamlit as st
import random
import json
import os
import boto3
from pymongo import MongoClient
from bson.objectid import ObjectId

# Constants
BOARD_SIZE = 10
EMPTY = ':ocean:'
HIT = ':boom:'
MISS = ':heavy_multiplication_x:'
SHIPS = [
    {"name": "Carrier", "size": 5, "symbol": ":ship:"},
    {"name": "Battleship", "size": 4, "symbol": ":motor_boat:"},
    {"name": "Cruiser", "size": 3, "symbol": ":boat:"},
    {"name": "Submarine", "size": 3, "symbol": ":ferry:"},
    {"name": "Destroyer", "size": 2, "symbol": ":speedboat:"}
]

# MongoDB Atlas Connection
client = MongoClient(os.environ.get('MONGODB_ATLAS_URI'))
db = client['battleship']
games = db['games']

# AWS Bedrock Client Setup
bedrock_runtime = boto3.client('bedrock-runtime',
                               aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                               aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
                               region_name="us-east-1")

def get_bedrock_claude_move(board, openent_moves=None):
    """
    Get the next move from Claude AI using AWS Bedrock.
    """
    print("inside get_bedrock_claude_move")
    claude_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 5000,
        "temperature": 0,
        "system": f"Please provide the next move as an opponent in the battleship game , the board is {BOARD_SIZE} X {BOARD_SIZE} . Be smart and stratigic. Respond only in JSON format strictly: 'row' : ... , 'col' : ... , 'entertainment_comment'  and nothing more  . ",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": f"The current board: {board} and your  moves were: {openent_moves if openent_moves else 'None'}"}
            ]
        }]
    })

    response = bedrock_runtime.invoke_model(
        body=claude_body,
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        accept="application/json",
        contentType="application/json",
    )

    response_body = json.loads(response.get("body").read())
    json_response = json.loads(response_body["content"][0]['text'])
    
    return json_response['row'], json_response['col'], json_response['entertainment_comment']

# Game Setup Functions
def create_empty_board():
    """Create an empty game board."""
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def place_ships_randomly(board):
    """Place ships randomly on the board."""
    for ship in SHIPS:
        while True:
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            direction = random.choice(['horizontal', 'vertical'])
            if can_place_ship(board, row, col, ship['size'], direction):
                place_ship(board, row, col, ship['size'], direction, ship['symbol'])
                break
    return board

def can_place_ship(board, row, col, size, direction):
    """Check if a ship can be placed at the given position."""
    if direction == 'horizontal':
        if col + size > BOARD_SIZE:
            return False
        return all(board[row][col+i] == EMPTY for i in range(size))
    else:
        if row + size > BOARD_SIZE:
            return False
        return all(board[row+i][col] == EMPTY for i in range(size))

def place_ship(board, row, col, size, direction, symbol):
    """Place a ship on the board."""
    if direction == 'horizontal':
        for i in range(size):
            board[row][col+i] = symbol
    else:
        for i in range(size):
            board[row+i][col] = symbol

def initialize_game():
    """Initialize the game state."""
    if 'game_state' not in st.session_state:
        st.session_state.game_state = {
            'player_board': place_ships_randomly(create_empty_board()),
            'opponent_board': place_ships_randomly(create_empty_board()),
            'player_attacks': create_empty_board(),
            'player_hits_left': 17,
            'opponent_attacks': create_empty_board(),
            'openent_moves': [],
            'opponent_hits_left': 17,
            'current_player': 'player',
            'game_state': 'not_started',
            'game_over': False,
            'message': ''
        }
    
    if 'game_id' not in st.session_state.game_state:
        st.session_state.game_state['game_id'] = ObjectId()
        gameId = st.session_state.game_state['game_id']
    
        # Initialize game data in MongoDB
        games.update_one({'game_id': gameId, 'type': 'player'},
                         {"$set": {'game_id': gameId,
                                   'board': st.session_state.game_state['player_board'],
                                   'attacking_board': st.session_state.game_state['player_attacks']}},
                         upsert=True)
        games.update_one({'game_id': gameId, 'type': 'opponent'},
                         {"$set": {'game_id': gameId, 
                                   'board': st.session_state.game_state['opponent_board'], 
                                   'oponent_moves': st.session_state.game_state['openent_moves'],
                                   'attacking_board': st.session_state.game_state['opponent_attacks']}},
                         upsert=True)

def check_game_over():
    """Check if the game is over."""
    game_state = st.session_state.game_state
    
    if game_state['player_hits_left'] == 0:
        game_state['message'] = "You won!"
        game_state['game_over'] = True
        return True
    elif game_state['opponent_hits_left'] == 0:
        game_state['message'] = "You lost!"
        game_state['game_over'] = True
        return True

def render_board(board, is_opponent=False):
    """Render the game board using Streamlit components."""
    for i, row in enumerate(board):
        cols = st.columns(BOARD_SIZE)
        for j, cell in enumerate(row):
            with cols[j]:
                if is_opponent and cell == EMPTY:
                    if st.button('🌊', key=f'opp_{i}_{j}', on_click=lambda r=i, c=j: attack(r, c)):
                        pass
                else:
                    # Determine the button color based on the cell content
                    if cell == EMPTY:
                        button_color = 'secondary'
                    elif cell in [HIT, MISS]:
                        button_color = 'primary'  # Use default color for hits and misses
                    else:
                        button_color = 'primary' if not is_opponent else 'secondary'
                    
                    # Use Streamlit's button with theme colors
                    st.button(cell, key=f'{"opp" if is_opponent else "player"}_{i}_{j}', type=button_color)

def attack(row, col):
    """Process a player's attack."""
    game_state = st.session_state.game_state
    if game_state['opponent_board'][row][col] != EMPTY:
        game_state['player_attacks'][row][col] = HIT
        game_state['message'] = "You hit a ship!"
        game_state['opponent_hits_left'] -= 1
    else:
        game_state['player_attacks'][row][col] = MISS
        game_state['message'] = "You missed!"
    
    update_database('player')
    game_state['current_player'] = 'opponent'

def update_database(type):
    """Update the game state in the database."""
    game_state = st.session_state.game_state
    gameId = game_state['game_id']
    games.update_one({'game_id': gameId, 'type': type},
                     {'$set': {'attacking_board': game_state['player_attacks'], 
                               'oponent_moves': game_state['openent_moves']}})

def opponent_turn():
    """Process the opponent's turn."""
    game_state = st.session_state.game_state
    with st.spinner("Opponent is making a move..."):
        opponent_doc = games.find_one({'game_id': ObjectId(game_state['game_id']), 'type': 'opponent'})
        print("opponent_doc:", opponent_doc)
        row, col, comment = get_bedrock_claude_move(opponent_doc['attacking_board'], openent_moves=opponent_doc['oponent_moves'])
        game_state['current_player'] = 'player'
        
        if game_state['player_board'][row][col] != EMPTY and game_state['opponent_attacks'][row][col] != MISS:
            game_state['openent_moves'].append({'row': row, 'col': col, 'status': 'hit'})
            game_state['opponent_attacks'][row][col] = HIT
            game_state['player_board'][row][col] = HIT
            game_state['player_hits_left'] -= 1
            game_state['message'] = f"Opponent hit your ship! Cell row {row} col {col} Opponent: {comment}"
        else:
            game_state['openent_moves'].append({'row': row, 'col': col, 'status': 'miss'})
            game_state['opponent_attacks'][row][col] = MISS
            game_state['player_board'][row][col] = MISS
            game_state['message'] = f"Opponent missed! Cell row {row} col {col}, Opponent: {comment}"

    update_database('opponent')
    game_state['current_player'] = 'player'

def main():
    """Main function to run the Battleship game."""
    st.title('Battleship Game')
    initialize_game()
    if st.session_state.game_state['game_over']:
        st.subheader('Game Over! You Lost!' if st.session_state.game_state['player_hits_left'] == 0 else 'You Won!')
    else:
        st.subheader('Your Turn')

    col1, col3, col2 = st.columns(3)
    with col1:
        st.subheader('Your Board')
        render_board(st.session_state.game_state['player_board'])

    with col3:
        st.subheader("Opponent Ships")
        for ship in SHIPS:
            my_ships, status = st.columns(2)
            with my_ships:
                st.write(f"  {ship['symbol']} {ship['name']}, size: {ship['size']}")
            with status:
                st.checkbox("Sunk", key=f"{ship['name']}_sunk")

        st.markdown("#### Opponent history")
        container = st.container(height=250)
        for move in st.session_state.game_state['openent_moves']:
            container.write(f"Row: {move['row']} Col: {move['col']} Status: {move['status']}")       

    with col2:
        st.subheader("Opponent's Board")
        render_board(st.session_state.game_state['player_attacks'], is_opponent=True)
    
    st.write(st.session_state.game_state['message'])
    
    if st.button('Reset Game'):
        st.session_state.clear()
        st.rerun()
    
    if st.session_state.game_state['current_player'] == 'opponent':
        opponent_turn()
        if check_game_over():
            st.session_state.game_state['current_player'] = 'game_over'
        else:
            st.rerun()
   
    st.header('Debug')
    expander = st.expander("Game State")
    for row in st.session_state.game_state['opponent_board']:
        expander.markdown(row)

    if st.button("Chat"):
        pop_chat()

if __name__ == '__main__':
    main()