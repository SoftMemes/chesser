import requests
import chess.pgn
import chess.engine
import io
import json
import os

# Get games from Chess.com
def download_chess_com_games(username, max_games=10):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36'
    }
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(url, headers=headers).json()
    archives = response['archives']

    # Retrieve games from the most recent archive
    recent_games_url = archives[-1]  # Most recent month of games
    games_response = requests.get(recent_games_url, headers=headers)
    games = games_response.json()['games']

    # Limit the number of games
    games_data = [{
        "id": game['uuid'],
        "end_time": game['end_time'],
        "time_control": game['time_control'],
        "time_class": game['time_class'],
        "pgn": game['pgn'],
        "white": {
            "username": game['white']['username'],
            "rating": game['white']['rating'],
            "result": game['white']['result'],
            "accuracy": game['accuracies']['white'] if game.get('accuracies', None) else None
        },
        "black": {
            "username": game['black']['username'],
            "rating": game['black']['rating'],
            "result": game['black']['result'],
            "accuracy": game['accuracies']['black'] if game.get('accuracies', None) else None
        }
    } for game in games[:max_games]]

    return games_data


def load_eco_pgn(filepath):
    eco_db = {}
    with open(filepath, 'r') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        while game is not None:
            eco_code = game.headers["ECO"]
            opening_name = game.headers["Opening"]
            variation = game.headers.get("Variation", None)
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
            eco_db[board.fen()] = (eco_code, opening_name, variation)
            game = chess.pgn.read_game(pgn_file)
    return eco_db


def analyze_game(pgn_game, output_dir, game_number, eco_db):
    # Initialize Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci("/home/freed/opt/stockfish/stockfish")
    engine.configure({"Threads": 12})

    game = chess.pgn.read_game(io.StringIO(pgn_game))
    board = game.board()
    res = []

    move_counter = 1
    for move in game.mainline_moves():
        board.push(move)

        info = engine.analyse(board, chess.engine.Limit(depth=25), multipv=3)
        fen = board.fen()
        if fen in eco_db:
            eco_code, opening_name, opening_variation = eco_db[fen]
            opening_data = {
                "eco": eco_code,
                "name": opening_name,
                "variation": opening_variation
            }
        else:
            opening_data = None

        move_data = {
            "move": move.uci(),
            "variations": [],
            "opening": opening_data
        }

        print(f"Move: {move}, Score: {info[0]['score']} ({opening_data.get('name', None) if opening_data else None})")

        for variation in info:
            score = variation['score'].relative
            mate = score.mate()  # This returns None if no mate, otherwise the number of moves to mate

            variation_data = {
                "depth": variation['depth'],
                "eval": score.score(mate_score=10000) if mate is None else None,
                "mate": mate,
                "pv": [mv.uci() for mv in variation['pv']] if variation.get('pv', None) else None,
            }
            move_data["variations"].append(variation_data)

        res.append(move_data)
        move_counter += 1

    engine.quit()

    return res


# Main function to download and analyze games
def main():
    username = "johnlocke999"
    output_dir = "./chess_analysis"
    eco_db = load_eco_pgn('eco.pgn')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    games = download_chess_com_games(username, max_games=1000)

    for i, game in enumerate(games):
        print(f"Analyzing game {i+1}...")
        moves = analyze_game(game['pgn'], output_dir, i+1, eco_db)
        output_file = os.path.join(output_dir, f"{game['id']}.json")
        # If the output file already exists, skip
        if os.path.exists(output_file):
            print(f"Not analyzing {game['id']}, already exists")
            continue
        game_data = {
            **game,
            "moves": moves
        }
        with open(output_file, 'w') as json_file:
            json.dump(game_data, json_file, indent=4)

if __name__ == "__main__":
    main()
