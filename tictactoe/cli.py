"""The terminal game."""

import argparse
import sys
from pathlib import Path

from .ai import best_move
from .board import CELLS, O, X, new_board, render
from .game import available, current_mark, is_over, outcome, place, winner

DEFAULT_LOG = "~/.tictactoe/games.log"


def main(argv=None):
    """Play a game and return the exit status."""
    parser = argparse.ArgumentParser(
        prog="tictactoe",
        description="Play noughts and crosses in the terminal.",
    )
    parser.add_argument(
        "--two-player",
        action="store_true",
        help="play against another person rather than the computer",
    )
    parser.add_argument(
        "--mark",
        choices=[X, O],
        default=X,
        help="the mark you play against the computer, X opening (default: X)",
    )
    parser.add_argument(
        "--log",
        metavar="PATH",
        default=DEFAULT_LOG,
        help=f"the file a finished game is appended to (default: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--player",
        metavar="NAME",
        default="",
        help="the name recorded in the log alongside the game",
    )
    args = parser.parse_args(argv)

    board = new_board()
    played = []
    print(render(board), end="\n\n")

    while not is_over(board):
        mark = current_mark(board)
        if args.two_player or mark == args.mark:
            cell = ask(board, mark)
            if cell is None:
                print("\nGame abandoned.")
                return 1
        else:
            cell = best_move(board, mark)
            print(f"The computer plays {mark} in cell {cell + 1}.")
        board = place(board, cell, mark)
        played.append(cell)
        print(render(board), end="\n\n")

    print(verdict(board))
    record(args.log, log_line(board, played, args.player))
    return 0


def ask(board, mark):
    """Read a legal cell from the player, or None if they are done.

    Anything that is not a free cell is answered and asked again, so a typo
    costs a line rather than the game.
    """
    free = ", ".join(str(cell + 1) for cell in available(board))
    while True:
        try:
            answer = input(f"{mark} plays which cell? ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if answer.lower() in ("q", "quit"):
            return None

        try:
            cell = int(answer) - 1
        except ValueError:
            print(f"Type a cell number from 1 to {CELLS}, or q to give up.")
            continue

        if cell not in available(board):
            print(f"Cell {answer} is not free. Free cells: {free}.")
            continue

        return cell


def verdict(board):
    """Return the closing line for a finished game."""
    won = winner(board)
    return f"{won} wins." if won is not None else "A draw."


def log_line(board, played, player):
    """Return the log entry for a finished game, without a line ending.

    The outcome is X, O or draw, and the cells are numbered from 1 as they are
    on screen. The name goes last and has any control characters replaced, so
    whatever was typed for it cannot split the entry across lines.
    """
    cells = ",".join(str(cell + 1) for cell in played)
    name = "".join(character if character.isprintable() else " " for character in player)
    return f"{outcome(board)}\t{cells}\t{name}"


def record(path, line):
    """Append `line` to the log at `path`, creating its directory if needed.

    A log that cannot be written is reported on stderr rather than turning a
    finished game into a failed one.
    """
    destination = Path(path).expanduser()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as log:
            log.write(line + "\n")
    except OSError as error:
        print(f"tictactoe: could not write the game log: {error}", file=sys.stderr)
