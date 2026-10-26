# Chess Puzzle Desktop Widget

A small always-on-top window with chess puzzles from the [Lichess](https://lichess.org) public API. I keep it on screen to solve a puzzle while waiting for a long-running AI prompt; it stays out of the way of other windows.

## Features

- Loads the next puzzle from `https://lichess.org/api/puzzle/next` (no account needed)
- Click-to-move with legal-move indicators
- Two-stage hint (first the piece to move, then the target square)
- Opponent replies are played automatically after each correct move
- Green flash on a correct move, red flash on a wrong one
- Shows the puzzle rating and up to three themes
- Flip board, skip to the next puzzle

## Requirements

- Python 3 with Tkinter
- `python-chess`, `requests` and `Pillow`
- A chess piece sprite sheet (not included in the repo, see below)

## Setup and running

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt pillow   # Pillow is not listed in requirements.txt
venv/bin/python app.py
```

Buttons at the bottom:

| Button | Action |
|--------|--------|
| **Hint** | First press highlights the piece to move, second press the destination |
| **Next →** | Load a new puzzle |
| **Flip** | Flip the board |

## Sprite sheet

`app.py` loads the pieces from `../../Chess_Pieces_Sprite.png` relative to itself. Change `SPRITE_PATH` at the top of `app.py` to use another location. Image files are ignored by `.gitignore`.

The image must be a 6 × 2 grid (any resolution):

```
[ K ][ Q ][ B ][ N ][ R ][ P ]   ← White (row 0)
[ k ][ q ][ b ][ n ][ r ][ p ]   ← Black (row 1)
```

## Tests

There are no tests.

## Structure

```
app.py            the whole application (Tkinter UI, puzzle logic, Lichess client)
requirements.txt  python-chess, requests
```

Built with the help of AI coding tools.
