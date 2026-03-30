"""
code1_mouse.py  —  RIGHT HAND: mouse control + draw support when draw mode active.

Features:
  • Index finger up + only = move cursor (smooth, fast)
  • Thumb + Index  pinch   = LEFT CLICK   (threshold 85px)
  • Thumb + Middle pinch   = RIGHT CLICK  (threshold 85px)
  • Index+Mid+Ring up      = SCROLL UP
  • All 4 up               = SCROLL DOWN
  • Pinky only up          = VOLUME (thumb up/dn)
  • All fingers closed     = BRIGHTNESS (thumb up/dn)
  • Index+Middle only      = SCREENSHOT
  • DRAW MODE active + Thumb+Middle close (<55px) = draw on shared canvas (blue)
  • Big gesture-popup overlay so user always sees what fired
"""

import pyautogui
import math
import time
import cv2
import shared_state

try:
    import screen_brightness_control as sbc
    SBC_OK = True
except Exception:
    SBC_OK = False

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0

screen_w, screen_h = pyautogui.size()

click_time      = 0.0
action_time     = 0.0
screenshot_time = 0.0

# Sticky gesture popup
_last_label = "Point index finger to move mouse"
_last_time  = 0.0
_last_color = (0, 200, 255)

# Right-hand draw trail
_rh_draw_prev = None


# ===== HELPERS =====
def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _fingers_up(lm):
    return [
        lm[8].y  < lm[6].y,    # index
        lm[12].y < lm[10].y,   # middle
        lm[16].y < lm[14].y,   # ring
        lm[20].y < lm[18].y,   # pinky
    ]


def _thumb_up(lm):
    """Thumb tip clearly above the thumb base (roughly 'thumbs up')."""
    return lm[4].y < lm[2].y


# ===== GESTURE POPUP =====
def _popup(frame, label, color, w, h):
    ol = frame.copy()
    cv2.rectangle(ol, (0, 40), (min(w - 340, 680), 105), (8, 8, 18), -1)
    cv2.addWeighted(ol, 0.72, frame, 0.28, 0, frame)
    cv2.rectangle(frame, (0, 40), (6, 105), color, -1)          # accent bar
    cv2.putText(frame, label, (14, 88),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)


def _guide(frame):
    cv2.rectangle(frame, (0, 40), (540, 74), (8, 8, 18), -1)
    cv2.putText(frame, "Raise index finger  ->  move mouse",
                (10, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (90, 90, 110), 1)


# ===== FINGER BAR =====
def _finger_bar(frame, fingers, w, h):
    labels = ["INDEX", "MIDDLE", "RING", "PINKY"]
    bw, bh = 82, 26
    x0 = 10
    y0 = h - bh - 6
    for lbl, state in zip(labels, fingers):
        col = (0, 210, 70) if state else (55, 55, 75)
        cv2.rectangle(frame, (x0, y0), (x0 + bw, y0 + bh), (16, 16, 22), -1)
        cv2.rectangle(frame, (x0, y0), (x0 + bw, y0 + bh), col, 2)
        cv2.putText(frame, ("UP " if state else "dn ") + lbl,
                    (x0 + 4, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.34, col, 1)
        x0 += bw + 5


# ===== PINCH INDICATOR =====
def _pinch_vis(frame, tx, ty, ix, iy, dist_ti, dist_tm):
    """Draw thumb→index pinch arc and thumb→middle arc."""
    def _arc(p1, p2, d, thr, color_close, color_far):
        col = color_close if d < thr else color_far
        cv2.line(frame, p1, p2, col, 2)
        mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
        cv2.circle(frame, mid, 16, (14, 14, 22), -1)
        cv2.putText(frame, str(int(d)), (mid[0]-12, mid[1]+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1)

    mx_approx = (tx + ix) // 2           # rough middle finger position for display
    _arc((tx, ty), (ix, iy), dist_ti, 85, (0, 255, 80),  (120, 120, 120))


# ===== MAIN =====
def process_hand(frame, handLms):
    global click_time, action_time, screenshot_time
    global _last_label, _last_time, _last_color, _rh_draw_prev

    h, w, _ = frame.shape
    shared_state.init_canvas(h, w)

    lm = handLms.landmark
    ix, iy = int(lm[8].x * w),  int(lm[8].y * h)
    mx, my = int(lm[12].x * w), int(lm[12].y * h)
    tx, ty = int(lm[4].x * w),  int(lm[4].y * h)

    sx = int(lm[8].x * screen_w)
    sy = int(lm[8].y * screen_h)

    dist_ti = _dist((ix, iy), (tx, ty))
    dist_tm = _dist((mx, my), (tx, ty))

    fingers = _fingers_up(lm)
    now     = time.time()

    label  = None
    color  = (0, 255, 100)
    done   = False

    # ===== DRAW MODE — right hand draws with thumb+middle pinch =====
    if shared_state.draw_mode:
        if dist_tm < 55:
            mid_pt = ((tx + mx) // 2, (ty + my) // 2)
            if _rh_draw_prev:
                cv2.line(shared_state.canvas, _rh_draw_prev, mid_pt,
                         shared_state.DRAW_COLOR_RIGHT, shared_state.DRAW_THICKNESS)
            else:
                cv2.circle(shared_state.canvas, mid_pt,
                           shared_state.DRAW_THICKNESS // 2,
                           shared_state.DRAW_COLOR_RIGHT, -1)
            _rh_draw_prev = mid_pt
            label = "DRAWING (thumb+middle)"
            color = (50, 80, 255)
            done  = True
        else:
            _rh_draw_prev = None

    # ===== LEFT CLICK (thumb + index pinch) =====
    if not done and dist_ti < 85 and now - click_time > 1.0:
        try: pyautogui.click()
        except: pass
        click_time = now
        label = "LEFT CLICK"
        color = (0, 255, 80)
        done  = True

    # ===== RIGHT CLICK (thumb + middle pinch) =====
    elif not done and dist_tm < 85 and now - click_time > 1.0:
        try: pyautogui.rightClick()
        except: pass
        click_time = now
        label = "RIGHT CLICK"
        color = (80, 200, 255)
        done  = True

    # ===== SCROLL UP (index + middle + ring) =====
    elif not done and fingers == [True, True, True, False] and now - action_time > 0.5:
        try: pyautogui.scroll(300)
        except: pass
        action_time = now
        label = "SCROLL UP"
        color = (255, 200, 0)
        done  = True

    # ===== SCROLL DOWN (all 4) =====
    elif not done and fingers == [True, True, True, True] and now - action_time > 0.5:
        try: pyautogui.scroll(-300)
        except: pass
        action_time = now
        label = "SCROLL DOWN"
        color = (255, 140, 0)
        done  = True

    # ===== BRIGHTNESS (fist, thumb up/dn) =====
    elif not done and fingers == [False, False, False, False] and now - action_time > 1.2:
        try:
            if _thumb_up(lm):
                if SBC_OK: sbc.set_brightness(80)
                label = "BRIGHTNESS UP"
            else:
                if SBC_OK: sbc.set_brightness(30)
                label = "BRIGHTNESS DOWN"
        except: pass
        action_time = now
        color = (200, 255, 80)
        done = True

    # ===== VOLUME (pinky only, thumb up/dn) =====
    elif not done and fingers[3] and not any(fingers[:3]) and now - action_time > 0.8:
        try:
            if _thumb_up(lm):
                pyautogui.press("volumeup")
                label = "VOLUME UP"
            else:
                pyautogui.press("volumedown")
                label = "VOLUME DOWN"
        except: pass
        action_time = now
        color = (255, 100, 200)
        done = True

    # ===== SCREENSHOT (index + middle only) =====
    elif not done and fingers == [True, True, False, False] and now - screenshot_time > 2.5:
        try:
            fn = f"screenshot_{int(now)}.png"
            pyautogui.screenshot(fn)
            label = "SCREENSHOT SAVED"
            color = (200, 100, 255)
        except: pass
        screenshot_time = now
        done = True

    # ===== MOVE CURSOR (index finger only) =====
    if not done and fingers == [True, False, False, False]:
        try: pyautogui.moveTo(sx, sy, duration=0.02)
        except: pass
        label = "MOVING CURSOR"
        color = (0, 200, 255)

    # ===== UPDATE STICKY POPUP =====
    if label:
        _last_label = label
        _last_time  = now
        _last_color = color

    # ===== VISUALS =====
    # Index tip
    cv2.circle(frame, (ix, iy), 14, (255, 80, 0), -1)
    cv2.circle(frame, (ix, iy), 14, (255, 255, 255), 2)
    # Thumb tip
    cv2.circle(frame, (tx, ty), 10, (0, 200, 255), -1)
    cv2.circle(frame, (tx, ty), 10, (255, 255, 255), 2)
    # Pinch line
    _pinch_vis(frame, tx, ty, ix, iy, dist_ti, dist_tm)

    # Draw-mode indicator for right hand
    if shared_state.draw_mode:
        cv2.putText(frame, "DRAW MODE — pinch thumb+middle to draw",
                    (10, h - 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 80, 255), 2)

    # Gesture popup (stays 1.5 s)
    age = now - _last_time
    if age < 1.5:
        _popup(frame, _last_label, _last_color, w, h)
    else:
        _guide(frame)

    # Finger state bars
    _finger_bar(frame, fingers, w, h)