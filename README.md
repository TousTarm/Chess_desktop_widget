# Chess Puzzle Desktop Widget

A lightweight desktop chess puzzle trainer powered by the [Lichess](https://lichess.org) public API. Runs as a always-on-top window so you can drill tactics between tasks.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Fetches random rated puzzles from Lichess in real time
- Click-to-move interface with legal-move indicators
- Two-stage hint system (highlight piece → highlight destination)
- Auto-plays opponent responses after each correct move
- Flip board, animated feedback (green flash / red flash)
- Displays puzzle rating and themes

## Requirements

- Python 3.8+
- A chess piece sprite sheet at `../../Chess_Pieces_Sprite.png` relative to `app.py`  
  (standard 6-column × 2-row layout: White on row 0, Black on row 1; columns: King, Queen, Bishop, Knight, Rook, Pawn)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

The window stays on top of other applications. Use the buttons at the bottom:

| Button | Action |
|--------|--------|
| **Hint** | First press highlights the piece to move; second press reveals the destination |
| **Next →** | Skip to a new puzzle |
| **Flip** | Flip the board orientation |

## Sprite Sheet

The app expects a sprite sheet at `../../Chess_Pieces_Sprite.png` (two levels up from `app.py`). You can change `SPRITE_PATH` at the top of `app.py` to point anywhere you like.

Expected layout (any resolution, must be 6 wide × 2 tall grid):

```
[ K ][ Q ][ B ][ N ][ R ][ P ]   ← White (row 0)
[ k ][ q ][ b ][ n ][ r ][ p ]   ← Black (row 1)
```

## Project Structure

```
Chess_desktop_widget/
├── app.py            # Main application
├── requirements.txt  # Python dependencies
└── README.md
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-chess` | Board representation, move generation, PGN parsing |
| `requests` | Lichess API HTTP calls |
| `Pillow` | Sprite sheet loading and image resizing |
| `tkinter` | GUI (bundled with Python) |
