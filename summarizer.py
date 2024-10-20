import chess
import json
from collections import Counter
import glob
import os

def piece_value(piece: chess.Piece):
    match piece.piece_type:
        case chess.PAWN:
            return 1
        case chess.KNIGHT:
            return 3
        case chess.BISHOP:
            return 3
        case chess.ROOK:
            return 5
        case chess.QUEEN:
            return 9
        case chess.KING:
            return 0

def is_endgame(current_pieces):
    # Using an arbitrary definition from https://en.wikipedia.org/wiki/Chess_endgame
    # "Speelman considers that endgames are positions in which each player has thirteen or fewer points in material (not counting the king)"
    white_piece_values = sum(piece_value(piece) for piece in current_pieces if piece.color == chess.WHITE)
    black_piece_values = sum(piece_value(piece) for piece in current_pieces if piece.color == chess.BLACK)
    return white_piece_values <= 13 and black_piece_values <= 13

def summarize_game(game):
    board = chess.Board()
    current_pieces = Counter(board.piece_map().values())
    captured_pieces = []
    has_entered_endgame = False

    for move_data in game['moves']:
        print(f'Now: https://lichess.org/analysis/standard/{board.fen()}')
        move = board.parse_san(move_data['move'])

        # Check if the move is a capture
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            print(f"Capture: {captured_piece} at {chess.square_name(move.to_square)}")

        board.push(move)
        pieces_after_move = Counter(board.piece_map().values())
        captured_pieces_in_move = current_pieces - pieces_after_move
        current_pieces = Counter(board.piece_map().values())
        captured_pieces.extend(captured_pieces_in_move.elements())

        if is_endgame(current_pieces.elements()) and not has_entered_endgame:
            print(f'Entering endgame: https://lichess.org/analysis/standard/{board.fen()}')
            has_entered_endgame = True


def get_openings(game):
    return (
            [move['opening']['name'] for move in game['moves'] if 'opening' in move and move['opening']] +
            [move['opening']['name'] + " - " + move['opening']['variation'] for move in game['moves'] if 'opening' in move and move['opening'] and 'variation' in move['opening'] and move['opening']['variation']]
    )

def won_game(game, username):
    return game['white']['username'] == username and game['white']['result'] == 'win' or game['black']['username'] == username and game['black']['result'] == 'win'

def player_color(game, username):
    if game['white']['username'] == username:
        return 'white'
    elif game['black']['username'] == username:
        return 'black'
    else:
        return None

def summarize_games(username):
    outcome_by_opening = {}
    win_by_color = {'white': 0, 'black': 0}
    total_games = 0

    for file in glob.glob(os.path.join('./chess_analysis', '*.json')):
        with open(file) as f:
            game = json.load(f)
            openings = get_openings(game)
            won = won_game(game, username)
            color = player_color(game, username)
            for opening in openings:
                if opening not in outcome_by_opening:
                    outcome_by_opening[opening] = {'won': 0, 'lost': 0}
                if won:
                    outcome_by_opening[opening]['won'] += 1
                else:
                    outcome_by_opening[opening]['lost'] += 1

            if won:
                win_by_color[color] += 1
            total_games += 1


    return outcome_by_opening, win_by_color, total_games






def main():
    res = summarize_games('JohnLocke999')
    pass


if __name__ == "__main__":
    main()


# Won/lost at stage (opening, middle, end)
# Resigned when shouldn't
# Number of blunders
# What was the move that lost the game, and at what stage
# Endgames with advantage/disadvantage/in between, conversion to win
# Wins as black/white
# Wins/losses by opening
