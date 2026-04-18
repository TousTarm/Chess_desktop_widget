#!/usr/bin/env python3
"""Chess Puzzle Desktop App — Lichess powered"""

import tkinter as tk
import chess
import chess.pgn
import io
import os
import requests
import threading
from PIL import Image, ImageTk

# ── Layout ───────────────────────────────────────────────────────────────────
BOARD_PX   = 600
SQ         = BOARD_PX // 8          # 75 px per square
PIECE_PX   = SQ - 6                 # piece image size with small margin

# ── Sprite sheet layout ───────────────────────────────────────────────────────
# Row 0 = White, Row 1 = Black
# Cols: King=0, Queen=1, Bishop=2, Knight=3, Rook=4, Pawn=5
SPRITE_PATH = os.path.join(os.path.dirname(__file__),
                            "../../Chess_Pieces_Sprite.png")
SPRITE_COL  = {
    chess.KING:   0, chess.QUEEN:  1, chess.BISHOP: 2,
    chess.KNIGHT: 3, chess.ROOK:   4, chess.PAWN:   5,
}

# ── Colours ───────────────────────────────────────────────────────────────────
C_LIGHT        = "#EEEED2"
C_DARK         = "#769656"
C_SEL_LIGHT    = "#F6F669"
C_SEL_DARK     = "#BBBB44"
C_LAST_LIGHT   = "#CDD26A"
C_LAST_DARK    = "#AABA44"
C_HINT_LIGHT   = "#F0C040"
C_HINT_DARK    = "#C09828"
C_BAR          = "#1E1E1E"
C_TOPBAR       = "#161616"
C_BTN          = "#3A3A3A"
C_BTN_ACTIVE   = "#555555"
C_WHITE_IND    = "#E8E8E8"
C_BLACK_IND    = "#888888"
C_TEXT         = "#FFFFFF"
C_SUBTEXT      = "#999999"

LICHESS_URL = "https://lichess.org/api/puzzle/next"

BTN_W = 10   # uniform button width (chars)


# ─────────────────────────────────────────────────────────────────────────────
def load_piece_images(path, size):
    """Return dict[(color, piece_type)] = PhotoImage, resized to size×size."""
    img      = Image.open(path).convert("RGBA")
    cell_w   = img.width  // 6
    cell_h   = img.height // 2
    images   = {}
    for ptype, col in SPRITE_COL.items():
        for color, row in ((chess.WHITE, 0), (chess.BLACK, 1)):
            x0, y0 = col * cell_w, row * cell_h
            crop   = img.crop((x0, y0, x0 + cell_w, y0 + cell_h))
            crop   = crop.resize((size, size), Image.LANCZOS)
            images[(color, ptype)] = ImageTk.PhotoImage(crop)
    return images


# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chess Puzzles")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg=C_BAR)

        # ── piece images ──
        self._pieces = load_piece_images(SPRITE_PATH, PIECE_PX)

        # ── state ──
        self.board        = chess.Board()
        self.solution     = []
        self.sol_idx      = 0
        self.player_color = chess.WHITE
        self.selected_sq  = None
        self.last_move    = None
        self.hint_sq      = None      # from_square highlight
        self.hint_to_sq   = None      # to_square highlight (2nd hint press)
        self.hint_level   = 0         # 0=none, 1=from, 2=from+to
        self.flipped      = False
        self.complete     = False
        self.anim_id      = None

        self._build_ui()
        self.load_puzzle()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── top bar ──
        top = tk.Frame(self, bg=C_TOPBAR, height=38)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        self._turn_canvas = tk.Canvas(top, width=18, height=18,
                                       bg=C_TOPBAR, highlightthickness=0)
        self._turn_canvas.pack(side=tk.LEFT, padx=(12, 4), pady=10)

        self._turn_var = tk.StringVar(value="")
        tk.Label(top, textvariable=self._turn_var,
                 bg=C_TOPBAR, fg=C_TEXT,
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT)

        self._rating = tk.StringVar(value="")
        tk.Label(top, textvariable=self._rating,
                 bg=C_TOPBAR, fg=C_SUBTEXT,
                 font=("Arial", 10)).pack(side=tk.RIGHT, padx=12)

        # ── board canvas ──
        self.cv = tk.Canvas(self, width=BOARD_PX, height=BOARD_PX,
                            highlightthickness=0, cursor="hand2")
        self.cv.pack()
        self.cv.bind("<Button-1>", self._on_click)

        # ── status bar ──
        sbar = tk.Frame(self, bg=C_BAR, height=28)
        sbar.pack(fill=tk.X)
        sbar.pack_propagate(False)

        self._status = tk.StringVar(value="Loading…")
        tk.Label(sbar, textvariable=self._status,
                 bg=C_BAR, fg=C_TEXT,
                 font=("Arial", 10)).pack(expand=True)

        # ── button bar ──
        bbar = tk.Frame(self, bg=C_BAR)
        bbar.pack(fill=tk.X)

        bkw = dict(bg=C_BTN, fg=C_TEXT, relief=tk.FLAT,
                   font=("Arial", 10, "bold"),
                   pady=7, cursor="hand2",
                   activebackground=C_BTN_ACTIVE, activeforeground=C_TEXT,
                   bd=0)

        self._hint_btn = tk.Button(bbar, text="Hint",
                                   command=self._show_hint, **bkw)
        self._hint_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(bbar, text="Next →",
                  command=self.load_puzzle, **bkw).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(bbar, text="Flip",
                  command=self._flip, **bkw).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _update_topbar(self):
        """Refresh the top bar — dot and label show player's fixed colour."""
        self._turn_canvas.delete("all")
        if self.player_color == chess.WHITE:
            self._turn_canvas.create_oval(1, 1, 17, 17,
                                           fill=C_WHITE_IND, outline="#666666")
        else:
            self._turn_canvas.create_oval(1, 1, 17, 17,
                                           fill="#222222", outline="#888888")

        color_name = "White" if self.player_color == chess.WHITE else "Black"

        if self.complete:
            self._turn_var.set("Puzzle solved!")
        else:
            self._turn_var.set(f"You play as {color_name}")

    # ── Coordinate helpers ────────────────────────────────────────────────────
    def _sq_xy(self, sq):
        c = chess.square_file(sq)
        r = chess.square_rank(sq)
        if not self.flipped:
            return c * SQ, (7 - r) * SQ
        return (7 - c) * SQ, r * SQ

    def _xy_sq(self, x, y):
        c, r = x // SQ, y // SQ
        if not self.flipped:
            return chess.square(c, 7 - r)
        return chess.square(7 - c, r)

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        self.cv.delete("board")
        self._update_topbar()

        # squares
        for sq in chess.SQUARES:
            x, y  = self._sq_xy(sq)
            light = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
            col   = C_LIGHT if light else C_DARK

            if self.last_move and sq in (self.last_move.from_square,
                                         self.last_move.to_square):
                col = C_LAST_LIGHT if light else C_LAST_DARK
            if sq == self.selected_sq:
                col = C_SEL_LIGHT if light else C_SEL_DARK
            if sq == self.hint_sq:
                col = C_HINT_LIGHT if light else C_HINT_DARK
            if sq == self.hint_to_sq:
                col = "#E8A020" if light else "#B07010"

            self.cv.create_rectangle(x, y, x + SQ, y + SQ,
                                     fill=col, outline="", tags="board")

        # coordinate labels
        for i in range(8):
            rank_lbl = str(8 - i) if not self.flipped else str(i + 1)
            file_lbl = "abcdefgh"[i] if not self.flipped else "hgfedcba"[i]
            fg_rank  = C_DARK  if (i % 2 == 0) else C_LIGHT
            fg_file  = C_DARK  if (i % 2 == 1) else C_LIGHT
            self.cv.create_text(3, i * SQ + 9, text=rank_lbl,
                                 anchor=tk.NW, font=("Arial", 9, "bold"),
                                 fill=fg_rank, tags="board")
            self.cv.create_text(i * SQ + SQ - 3, BOARD_PX - 3,
                                 text=file_lbl, anchor=tk.SE,
                                 font=("Arial", 9, "bold"),
                                 fill=fg_file, tags="board")

        # legal-move indicators (green)
        if self.selected_sq is not None:
            for mv in self.board.legal_moves:
                if mv.from_square != self.selected_sq:
                    continue
                x, y   = self._sq_xy(mv.to_square)
                cx, cy = x + SQ // 2, y + SQ // 2
                if self.board.piece_at(mv.to_square):
                    r = SQ // 2 - 3
                    self.cv.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        outline="#4CAF50", width=5,
                                        fill="", tags="board")
                else:
                    r = SQ // 6
                    self.cv.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill="#4CAF50", outline="",
                                        tags="board")

        # pieces (sprite images)
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue
            x, y   = self._sq_xy(sq)
            img    = self._pieces[(piece.color, piece.piece_type)]
            offset = (SQ - PIECE_PX) // 2
            self.cv.create_image(x + offset, y + offset,
                                  anchor=tk.NW, image=img, tags="board")

    # ── Input ─────────────────────────────────────────────────────────────────
    def _on_click(self, ev):
        if self.complete:
            return
        if self.board.turn != self.player_color:
            return

        sq    = self._xy_sq(ev.x, ev.y)
        piece = self.board.piece_at(sq)

        if self.selected_sq is None:
            if piece and piece.color == self.player_color:
                self.selected_sq = sq
                self.hint_sq     = None
                self._draw()
            return

        if sq == self.selected_sq:
            self.selected_sq = None
            self._draw()
            return

        if piece and piece.color == self.player_color:
            self.selected_sq = sq
            self._draw()
            return

        promo     = None
        src_piece = self.board.piece_at(self.selected_sq)
        if (src_piece and src_piece.piece_type == chess.PAWN
                and chess.square_rank(sq) in (0, 7)):
            promo = chess.QUEEN

        move = chess.Move(self.selected_sq, sq, promotion=promo)
        if move in self.board.legal_moves:
            self._try_move(move)
        else:
            self.selected_sq = None
            self._draw()

    # ── Puzzle logic ──────────────────────────────────────────────────────────
    def _try_move(self, move):
        if self.sol_idx >= len(self.solution):
            return
        expected = self.solution[self.sol_idx]

        def norm(m):
            u = m.uci()
            return u[:4] + ("q" if len(u) == 5 else "")

        if norm(move) == norm(expected):
            final = (move if not expected.promotion
                     else chess.Move(move.from_square, move.to_square,
                                     promotion=expected.promotion))
            self._correct(final)
        else:
            self._wrong()

    def _correct(self, move):
        self.board.push(move)
        self.last_move   = move
        self.selected_sq = None
        self.hint_sq     = None
        self.hint_to_sq  = None
        self.hint_level  = 0
        self.sol_idx    += 1
        self._draw()

        if self.sol_idx >= len(self.solution):
            self.complete = True
            self._status.set("Solved! ✓")
            self._update_topbar()
            self._flash_success()
            return

        self.after(800, self._computer_move)

    def _computer_move(self):
        if self.sol_idx >= len(self.solution):
            return
        move = self.solution[self.sol_idx]
        self.board.push(move)
        self.last_move = move
        self.sol_idx  += 1
        self._draw()

        if self.sol_idx >= len(self.solution):
            self.complete = True
            self._status.set("Solved! ✓")
            self._update_topbar()
            self._flash_success()
        else:
            self._status.set("Find the best move!")

    def _wrong(self):
        self.selected_sq = None
        self._draw()
        self._status.set("Not the right move — try again")
        self._flash_wrong()

    # ── Buttons ───────────────────────────────────────────────────────────────
    def _show_hint(self):
        if self.complete or self.sol_idx >= len(self.solution):
            return
        mv = self.solution[self.sol_idx]
        self.selected_sq = None
        if self.hint_level < 1:
            self.hint_sq    = mv.from_square
            self.hint_to_sq = None
            self.hint_level = 1
            self._status.set("Hint: move the highlighted piece")
        else:
            self.hint_sq    = mv.from_square
            self.hint_to_sq = mv.to_square
            self.hint_level = 2
            self._status.set("Hint: move to the darker square")
        self._draw()

    def _flip(self):
        self.flipped = not self.flipped
        self._draw()

    # ── Animations ────────────────────────────────────────────────────────────
    def _cancel_anim(self):
        if self.anim_id:
            self.after_cancel(self.anim_id)
            self.anim_id = None
        self.cv.delete("anim")

    def _flash_success(self):
        self._cancel_anim()
        self._anim_success(0)

    def _anim_success(self, frame):
        FRAMES = 22
        self.cv.delete("anim")
        if frame >= FRAMES:
            self._draw()
            return

        stipple = "gray12" if frame < 4 or frame > 17 else "gray25"
        self.cv.create_rectangle(0, 0, BOARD_PX, BOARD_PX,
                                  fill="#4CAF50", outline="",
                                  stipple=stipple, tags="anim")
        if frame >= 3:
            self.cv.create_text(BOARD_PX // 2, BOARD_PX // 2 - 20,
                                 text="✓", font=("Arial", 110, "bold"),
                                 fill="#FFFFFF", tags="anim")
            self.cv.create_text(BOARD_PX // 2, BOARD_PX // 2 + 80,
                                 text="Solved!", font=("Arial", 28, "bold"),
                                 fill="#FFFFFF", tags="anim")

        self.anim_id = self.after(65, lambda: self._anim_success(frame + 1))

    def _flash_wrong(self):
        self._cancel_anim()
        self._anim_wrong(0)

    def _anim_wrong(self, frame):
        FRAMES = 6
        self.cv.delete("anim")
        if frame >= FRAMES:
            self._draw()
            return

        if frame % 2 == 0:
            self.cv.create_rectangle(0, 0, BOARD_PX, BOARD_PX,
                                      fill="#C62828", outline="",
                                      stipple="gray25", tags="anim")
            self.cv.create_text(BOARD_PX // 2, BOARD_PX // 2,
                                 text="✗", font=("Arial", 100, "bold"),
                                 fill="#FFFFFF", tags="anim")

        self.anim_id = self.after(110, lambda: self._anim_wrong(frame + 1))

    # ── Network ───────────────────────────────────────────────────────────────
    def load_puzzle(self):
        self._cancel_anim()
        self.complete    = False
        self.selected_sq = None
        self.hint_sq     = None
        self.hint_to_sq  = None
        self.hint_level  = 0
        self.last_move   = None
        self.sol_idx     = 0
        self._status.set("Loading puzzle…")
        self._rating.set("")
        self._turn_var.set("Loading…")
        self._draw()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            r = requests.get(LICHESS_URL, timeout=10,
                             headers={"Accept": "application/json"})
            r.raise_for_status()
            self.after(0, lambda: self._setup(r.json()))
        except Exception as e:
            self.after(0, lambda: self._status.set(f"Network error: {e}"))

    def _setup(self, data):
        try:
            puzzle = data["puzzle"]
            game   = data["game"]

            pgn      = chess.pgn.read_game(io.StringIO(game["pgn"]))
            moves    = list(pgn.mainline_moves())
            init_ply = puzzle["initialPly"]
            sol0     = chess.Move.from_uci(puzzle["solution"][0])

            # Find the board position where sol0 is a legal move.
            # initialPly is not always exactly right — search nearby offsets.
            board = None
            chosen_n = init_ply - 1  # default fallback
            for offset in (1, 0, -1, 2, -2):
                n = init_ply - offset
                if not (0 <= n <= len(moves)):
                    continue
                b = pgn.board()
                for i, mv in enumerate(moves):
                    if i >= n:
                        break
                    b.push(mv)
                if sol0 in b.legal_moves:
                    board    = b
                    chosen_n = n
                    break

            if board is None:          # last resort: plain init_ply - 1
                board = pgn.board()
                for i, mv in enumerate(moves):
                    if i >= init_ply - 1:
                        break
                    board.push(mv)
                chosen_n = init_ply - 1

            self.board        = board
            self.player_color = board.turn
            self.flipped      = (self.player_color == chess.BLACK)
            self.last_move    = moves[chosen_n - 1] if chosen_n > 0 else None
            self.solution     = [chess.Move.from_uci(u)
                                  for u in puzzle["solution"]]

            rating = puzzle.get("rating", "?")
            themes = ", ".join(puzzle.get("themes", [])[:3])
            self._rating.set(f"★ {rating}" +
                             (f"  ·  {themes}" if themes else ""))

            self._status.set("Find the best move!")
            self._draw()

        except Exception as e:
            import traceback; traceback.print_exc()
            self._status.set(f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
