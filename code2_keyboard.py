"""
code2_keyboard.py  —  LEFT HAND: virtual keyboard + optional draw mode.

Stability fixes:
  • EMA position smoothing  (ALPHA = 0.45 → jitter removed)
  • Hysteresis detection    (expanded keep-zone so tiny wobbles don't reset hover)
  • Larger shrink margin    (finger must be well inside key to begin hover)
  • Longer thresholds       (0.9s hover, 1.1s cooldown)
  • Flash feedback          (key turns green after press)
  • Palm-open gesture holds 1.5 s → toggles draw mode
"""

import cv2
import pyautogui
import numpy as np
import time
import shared_state

# ===== KEYBOARD LAYOUT =====
keys = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["CAPS", "Z", "X", "C", "V", "B", "N", "M", "BACK"],
    ["DRAW", "SPACE", "CLR"]
]

KEY_W = 64
KEY_H = 52
GAP   = 9

# ===== STATE =====
hover_key  = None
hover_time = 0.0
last_click = 0.0
caps       = False

# Flash feedback
flash_key  = None
flash_time = 0.0

# Draw-mode: previous point for left-hand drawing
lh_draw_prev = None

# Palm-gesture tracking
_palm_held_since = 0.0

# ===== EMA SMOOTHING =====
_sx = None   # smoothed x
_sy = None   # smoothed y
_ALPHA = 0.45   # 0 = very smooth / slow,  1 = raw / fast

def _smooth(ix: int, iy: int):
    global _sx, _sy
    if _sx is None:
        _sx, _sy = float(ix), float(iy)
    _sx = _ALPHA * ix + (1 - _ALPHA) * _sx
    _sy = _ALPHA * iy + (1 - _ALPHA) * _sy
    return int(_sx), int(_sy)


# ===== KEY GEOMETRY =====
def _kb_start_y(h: int) -> int:
    return int(h * 0.55)

def _row_x(w: int, row: list) -> int:
    return (w - (len(row) * (KEY_W + GAP) - GAP)) // 2


# ===== STABLE KEY DETECTION (EMA + Hysteresis) =====
_hyst_bounds = None   # (x1, y1, x2, y2) – expanded zone of current hover key

def _detect_key_stable(ix: int, iy: int, w: int, h: int):
    global _hyst_bounds
    SHRINK = 8    # finger must be this far inside a key to start a hover
    EXPAND = 16   # once hovering, allow finger to drift this far outside before cancelling

    # ---- Hysteresis: still hovering? ----
    if _hyst_bounds and hover_key:
        hx1, hy1, hx2, hy2 = _hyst_bounds
        if hx1 - EXPAND < ix < hx2 + EXPAND and hy1 - EXPAND < iy < hy2 + EXPAND:
            return hover_key          # stay on the same key
        _hyst_bounds = None           # escaped the expand zone

    # ---- Fresh detection ----
    y = _kb_start_y(h)
    for row in keys:
        x = _row_x(w, row)
        for key in row:
            if x + SHRINK < ix < x + KEY_W - SHRINK and y + SHRINK < iy < y + KEY_H - SHRINK:
                _hyst_bounds = (x, y, x + KEY_W, y + KEY_H)
                return key
            x += KEY_W + GAP
        y += KEY_H + GAP
    return None


# ===== PALM DETECTION =====
def _palm_open(lm) -> bool:
    """All 4 fingers AND thumb clearly extended."""
    return (lm[8].y  < lm[5].y  and   # index
            lm[12].y < lm[9].y  and   # middle
            lm[16].y < lm[13].y and   # ring
            lm[20].y < lm[17].y and   # pinky
            lm[4].x  < lm[3].x)       # thumb stretched sideways (left hand)


# ===== DRAW KEYBOARD =====
def draw_keyboard(img):
    h, w, _ = img.shape
    y0  = _kb_start_y(h)
    now = time.time()

    # ---- Full-width dark background strip ----
    rows    = len(keys)
    kb_h    = rows * (KEY_H + GAP) + GAP
    cv2.rectangle(img, (0, y0 - GAP), (w, y0 + kb_h), (20, 20, 26), -1)
    cv2.line(img,      (0, y0 - GAP), (w, y0 - GAP),  (70, 70, 100), 2)

    # ---- DRAW MODE banner ----
    if shared_state.draw_mode:
        cv2.rectangle(img, (0, y0 - GAP - 28), (w, y0 - GAP), (0, 80, 0), -1)
        cv2.putText(img,
                    "  DRAW MODE ON  |  Hold open palm 1.5s OR hover DRAW to toggle  |  Hover CLR to erase",
                    (6, y0 - GAP - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 120), 1)

    # ---- Keys ----
    y = y0
    for row in keys:
        x = _row_x(w, row)
        for key in row:
            hovering   = (key == hover_key)
            flashing   = (key == flash_key and now - flash_time < 0.4)

            # Colour scheme
            if flashing:
                bg, fg, brd = (0, 210, 80),   (255, 255, 255), (0, 255, 120)
            elif hovering:
                bg, fg, brd = (40, 110, 210), (255, 255, 255), (80, 180, 255)
            elif key == "DRAW":
                active = shared_state.draw_mode
                bg  = (0, 150, 0)    if active else (45, 45, 70)
                brd = (0, 220, 0)    if active else (80, 80, 120)
                fg  = (255, 255, 255)
            elif key == "CLR":
                bg, fg, brd = (150, 25, 25),  (255, 255, 255), (210, 60, 60)
            elif key == "BACK":
                bg, fg, brd = (160, 35, 35),  (255, 255, 255), (220, 70, 70)
            elif key == "SPACE":
                bg, fg, brd = (35, 35, 58),   (170, 170, 255), (75, 75, 140)
            elif key == "CAPS":
                if caps:
                    bg, fg, brd = (190, 120, 0), (255, 255, 255), (255, 175, 0)
                else:
                    bg, fg, brd = (50, 42, 18),  (190, 170, 110), (95, 78, 38)
            else:
                bg, fg, brd = (205, 205, 218), (8, 8, 14), (120, 120, 145)

            # Shadow → face → border
            cv2.rectangle(img, (x+3, y+3), (x+KEY_W+3, y+KEY_H+3), (6, 6, 8), -1)
            cv2.rectangle(img, (x,   y),   (x+KEY_W,   y+KEY_H),   bg,         -1)
            cv2.rectangle(img, (x,   y),   (x+KEY_W,   y+KEY_H),   brd,  2 if hovering else 1)

            # Label
            fs   = 0.34 if len(key) > 3 else 0.50
            xoff = 3    if len(key) > 3 else 7
            cv2.putText(img, key, (x + xoff, y + 34),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, fg, 2)
            x += KEY_W + GAP
        y += KEY_H + GAP

    # CAPS indicator
    if caps:
        cv2.putText(img, "CAPS ON", (10, y0 - GAP - 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 196, 0), 2)


# ===== HOVER PROGRESS ARC =====
def _draw_hover_arc(frame, ix, iy, elapsed, threshold):
    pct   = min(elapsed / threshold, 1.0)
    angle = int(360 * pct)
    cv2.ellipse(frame, (ix, iy), (24, 24), -90, 0, angle, (0, 180, 255), 4)
    cv2.putText(frame, f"{int(pct * 100)}%", (ix - 16, iy + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 240, 255), 1)


# ===== MAIN =====
def process_hand(frame, hand):
    global hover_key, hover_time, last_click, caps
    global flash_key, flash_time, lh_draw_prev, _palm_held_since

    h, w, _ = frame.shape
    shared_state.init_canvas(h, w)

    lm = hand.landmark

    # --- Smooth finger position ---
    raw_ix = int(lm[8].x * w)
    raw_iy = int(lm[8].y * h)
    ix, iy = _smooth(raw_ix, raw_iy)

    # --- Palm gesture → toggle draw mode (hold 1.5 s) ---
    now = time.time()
    if _palm_open(lm):
        if _palm_held_since == 0.0:
            _palm_held_since = now
        elif now - _palm_held_since > 1.5:
            shared_state.draw_mode = not shared_state.draw_mode
            _palm_held_since = 0.0
            lh_draw_prev = None
    else:
        _palm_held_since = 0.0

    # --- Draw keyboard (always) ---
    draw_keyboard(frame)

    # --- Finger cursor dot ---
    cv2.circle(frame, (ix, iy), 12, (0, 240, 80), -1)
    cv2.circle(frame, (ix, iy), 12, (255, 255, 255), 2)

    # --- Left-hand draw on canvas (when draw mode + not over a key) ---
    key_under = _detect_key_stable(ix, iy, w, h)
    if shared_state.draw_mode and key_under is None:
        if lh_draw_prev is not None:
            cv2.line(shared_state.canvas, lh_draw_prev, (ix, iy),
                     shared_state.DRAW_COLOR_LEFT, shared_state.DRAW_THICKNESS)
        else:
            cv2.circle(shared_state.canvas, (ix, iy),
                       shared_state.DRAW_THICKNESS // 2,
                       shared_state.DRAW_COLOR_LEFT, -1)
        lh_draw_prev = (ix, iy)
    else:
        lh_draw_prev = None

    # ---- Key hover & click ----
    HOVER_THRESHOLD = 0.9
    COOLDOWN        = 1.1

    ret_char = ""
    key = key_under

    if key:
        if key != hover_key:
            hover_key  = key
            hover_time = now
        else:
            elapsed = now - hover_time
            _draw_hover_arc(frame, ix, iy, elapsed, HOVER_THRESHOLD)

            if elapsed > HOVER_THRESHOLD and now - last_click > COOLDOWN:

                if key == "SPACE":
                    pyautogui.press("space")
                    ret_char = " "
                elif key == "BACK":
                    pyautogui.press("backspace")
                    ret_char = "\b"
                elif key == "CAPS":
                    caps = not caps
                elif key == "DRAW":
                    shared_state.draw_mode = not shared_state.draw_mode
                    lh_draw_prev = None
                elif key == "CLR":
                    shared_state.clear_canvas()
                else:
                    ch = key if caps else key.lower()
                    pyautogui.write(ch)
                    ret_char = ch

                flash_key  = key
                flash_time = now
                last_click = now
                hover_key  = None
    else:
        hover_key = None

    return ret_char