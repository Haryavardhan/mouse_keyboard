import pyautogui
import math
import time
import screen_brightness_control as sbc

pyautogui.FAILSAFE = True

screen_w, screen_h = pyautogui.size()

click_time = 0
action_time = 0
screenshot_time = 0

# ===== HELPERS =====
def distance(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def finger_states(lm):
    return [
        lm[8].y < lm[6].y,
        lm[12].y < lm[10].y,
        lm[16].y < lm[14].y,
        lm[20].y < lm[18].y
    ]

def thumb_position(lm):
    return "up" if lm[4].y < lm[0].y else "down"


# ===== MAIN FUNCTION =====
def process_hand(frame, handLms):
    global click_time, action_time, screenshot_time

    h, w, _ = frame.shape
    lm = handLms.landmark

    ix, iy = int(lm[8].x * w), int(lm[8].y * h)
    mx, my = int(lm[12].x * w), int(lm[12].y * h)
    tx, ty = int(lm[4].x * w), int(lm[4].y * h)

    screen_x = int(lm[8].x * screen_w)
    screen_y = int(lm[8].y * screen_h)

    dist_thumb_index = distance((ix, iy), (tx, ty))
    dist_thumb_middle = distance((mx, my), (tx, ty))

    fingers = finger_states(lm)
    now = time.time()

    action_done = False

    # ===== LEFT CLICK =====
    if dist_thumb_index < 60 and now - click_time > 1:
        pyautogui.click()
        click_time = now
        action_done = True

    # ===== RIGHT CLICK =====
    elif dist_thumb_middle < 60 and now - click_time > 1:
        pyautogui.rightClick()
        click_time = now
        action_done = True

    # ===== SCROLL UP =====
    elif fingers == [True, True, True, False] and now - action_time > 0.6:
        pyautogui.scroll(300)
        action_time = now
        action_done = True

    # ===== SCROLL DOWN =====
    elif fingers == [True, True, True, True] and now - action_time > 0.6:
        pyautogui.scroll(-300)
        action_time = now
        action_done = True

    # ===== BRIGHTNESS =====
    elif fingers == [False, False, False, False] and now - action_time > 1:
        try:
            if thumb_position(lm) == "up":
                sbc.set_brightness(80)
            else:
                sbc.set_brightness(30)
        except:
            pass
        action_time = now
        action_done = True

    # ===== VOLUME =====
    elif fingers[3] and not any(fingers[:3]) and now - action_time > 0.8:
        if thumb_position(lm) == "up":
            pyautogui.press("volumeup")
        else:
            pyautogui.press("volumedown")
        action_time = now
        action_done = True

    # ===== SCREENSHOT =====
    elif fingers == [True, True, False, False] and now - screenshot_time > 2:
        filename = f"screenshot_{int(now)}.png"
        pyautogui.screenshot(filename)
        screenshot_time = now
        action_done = True

    # ===== MOVE CURSOR =====
    if not action_done and fingers == [True, False, False, False]:
        pyautogui.moveTo(screen_x, screen_y, duration=0.05)