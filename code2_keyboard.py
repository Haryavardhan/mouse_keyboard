import cv2
import pyautogui
import time

# ===== KEYBOARD =====
keys = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["CAPS","Z","X","C","V","B","N","M","BACK"],
    ["SPACE"]
]

KEY_W, KEY_H = 70, 60
GAP = 10

hover_key = None
hover_time = 0
last_click = 0
caps = False


# ===== DRAW =====
def draw_keyboard(img):
    h, w, _ = img.shape
    y = int(h * 0.2)

    for row in keys:
        x = (w - (len(row)*(KEY_W+GAP))) // 2

        for key in row:
            cv2.rectangle(img, (x,y), (x+KEY_W, y+KEY_H), (255,255,255), -1)
            cv2.rectangle(img, (x,y), (x+KEY_W, y+KEY_H), (0,0,0), 2)

            cv2.putText(img, key, (x+10, y+40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)

            x += KEY_W + GAP

        y += KEY_H + GAP


def detect_key(ix, iy, img):
    h, w, _ = img.shape
    y = int(h * 0.2)

    for row in keys:
        x = (w - (len(row)*(KEY_W+GAP))) // 2

        for key in row:
            if x < ix < x+KEY_W and y < iy < y+KEY_H:
                return key
            x += KEY_W + GAP

        y += KEY_H + GAP

    return None


# ===== MAIN FUNCTION =====
def process_hand(frame, hand):
    global hover_key, hover_time, last_click, caps

    h, w, _ = frame.shape

    draw_keyboard(frame)

    ix = int(hand.landmark[8].x * w)
    iy = int(hand.landmark[8].y * h)

    cv2.circle(frame, (ix, iy), 10, (0,255,0), -1)

    key = detect_key(ix, iy, frame)
    now = time.time()

    if key:
        if key != hover_key:
            hover_key = key
            hover_time = now

        elif now - hover_time > 0.5 and now - last_click > 0.7:

            if key == "SPACE":
                pyautogui.press("space")

            elif key == "BACK":
                pyautogui.press("backspace")

            elif key == "CAPS":
                caps = not caps

            else:
                ch = key if caps else key.lower()
                pyautogui.write(ch)

            last_click = now
            hover_key = None

    else:
        hover_key = None