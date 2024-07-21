# Battleship Game

This is a Streamlit-based implementation of the classic Battleship game, featuring a player versus an AI opponent powered by AWS Bedrock's Claude model.

## Features

- Interactive game board using Streamlit components
- AI opponent using AWS Bedrock's Claude model
- Game state persistence using MongoDB Atlas
- Randomized ship placement
- Turn-based gameplay

## Prerequisites

- Python 3.7+
- Streamlit
- pymongo
- boto3
- AWS account with Bedrock Claude 3.5 access on `US-EAST-1`.
- MongoDB Atlas account with your IP in the accesslist permission.

## Installation

1. Clone the repository:
```
cd atlas-ai-battleship-game
```
2. Install the required packages:
```
pip install -r requirements.txt
```
3. Set up environment variables:
- `MONGODB_ATLAS_URI`: Your MongoDB Atlas connection string
- `AWS_ACCESS_KEY`: Your AWS access key
- `AWS_SECRET_KEY`: Your AWS secret key

## Running the Game

To start the game, run:
```
streamlit run battleship_game.py
```

## How to Play

1. The game starts with ships randomly placed on both the player's and opponent's boards.
2. Click on the ocean emoji (🌊) on the attack board to make your move.
3. The AI opponent (Claude) will make its move automatically.
4. The game continues until all ships of one player are sunk.
5. You can mark the ships you have sank.

## Code Structure

- `main()`: The main function that sets up the Streamlit UI and game flow.
- `initialize_game()`: Initializes the game state and database entries.
- `render_board()`: Renders the game boards using Streamlit components.
- `attack()`: Processes a player's attack.
- `opponent_turn()`: Handles the AI opponent's turn using Claude.
- `get_bedrock_claude_move()`: Interacts with AWS Bedrock to get Claude's next move.
- `update_database()`: Updates the game state in the MongoDB database.

## Future Improvements

- Implement a more sophisticated AI strategy
- Add sound effects and animations
- Create a multiplayer mode
- Improve the UI/UX with more detailed ship information and game statistics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
