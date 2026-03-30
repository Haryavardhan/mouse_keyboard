"""
shared_state.py — Single source of truth shared between both hand modules.
Both code1_mouse (right hand) and code2_keyboard (left hand) read/write here.
"""
import numpy as np

# ===== DRAW MODE =====
draw_mode = False        # True = drawing canvas is active

# ===== CANVAS =====
canvas          = None
DRAW_COLOR_LEFT  = (0, 165, 255)   # Orange  – left hand draws
DRAW_COLOR_RIGHT = (50,  80, 255)  # Blue-ish – right hand draws
DRAW_THICKNESS   = 6


def init_canvas(h: int, w: int):
    global canvas
    if canvas is None or canvas.shape[0] != h or canvas.shape[1] != w:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)


def clear_canvas():
    global canvas
    if canvas is not None:
        canvas[:] = 0


def apply_canvas(frame):
    """Blit canvas drawing onto frame (non-black pixels only)."""
    if canvas is not None:
        mask = canvas.any(axis=2)
        frame[mask] = canvas[mask]
