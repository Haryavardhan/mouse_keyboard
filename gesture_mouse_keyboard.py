"""
gesture_mouse_keyboard.py  —  Main entry point

Layout  (display frame 1280×720):
  LEFT  half  →  shows LEFT  HAND   = KEYBOARD
  RIGHT half  →  shows RIGHT HAND   = MOUSE
  Tips panel  →  right-side column (always visible)

Extra features:
  • Console auto-minimises at startup  (camera window comes to front)
  • Voice command "stop" (or "stop mouse") → stops program, restores console
  • ESC / Q in camera window also stops cleanly
  • Mouse gestures keep working even when console is minimised
"""

import cv2
import mediapipe as mp
import time
import threading
import ctypes
import shared_state
import code1_mouse
import code2_keyboard

# ======================================================
# DISPLAY SIZE
# ======================================================
DISPLAY_W = 1280
DISPLAY_H = 720

# ======================================================
# CONSOLE MANAGEMENT  (Windows only – uses kernel32/user32)
# ======================================================
_console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()

def _minimize_console():
    if _console_hwnd:
        ctypes.windll.user32.ShowWindow(_console_hwnd, 6)   # SW_MINIMIZE

def _restore_console():
    if _console_hwnd:
        ctypes.windll.user32.ShowWindow(_console_hwnd, 9)   # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(_console_hwnd)

# ======================================================
# VOICE LISTENER  (runs in background thread)
# ======================================================
_stop_event = threading.Event()

def _voice_listener():
    """
    Listens for the keyword 'stop' using Google Speech Recognition.
    Falls back gracefully if microphone / library unavailable.
    """
    try:
        import speech_recognition as sr
        r   = sr.Recognizer()
        r.energy_threshold        = 300
        r.dynamic_energy_threshold = True

        print("[VOICE] Microphone ready — say  'STOP'  to end the program.")

        while not _stop_event.is_set():
            try:
                with sr.Microphone() as src:
                    r.adjust_for_ambient_noise(src, duration=0.3)
                    audio = r.listen(src, timeout=3, phrase_time_limit=4)
                text = r.recognize_google(audio).lower()
                print(f"[VOICE] Heard: '{text}'")
                if "stop" in text:
                    print("[VOICE] Stop command detected — closing …")
                    _stop_event.set()
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception:
                pass

    except ImportError:
        print("[VOICE] SpeechRecognition not available — press ESC or Q to stop.")
    except Exception as e:
        print(f"[VOICE] Could not start microphone: {e}  — press ESC or Q to stop.")


# ======================================================
# CAMERA
# ======================================================
print("Starting Gesture Mouse + Keyboard")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

time.sleep(1.5)

if not cap.isOpened():
    print("[X] Camera could not open")
    exit()

print("[OK] Camera opened — warming up …")
for _ in range(30):
    cap.read()
print("[OK] Camera ready!")

# ======================================================
# MEDIAPIPE
# ======================================================
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

_lm_spec   = mp_draw.DrawingSpec(color=(0, 255, 0),   thickness=2, circle_radius=4)
_conn_spec = mp_draw.DrawingSpec(color=(220, 220, 220), thickness=2)

# ======================================================
# START VOICE THREAD
# ======================================================
_vt = threading.Thread(target=_voice_listener, daemon=True)
_vt.start()

# Give voice thread a moment, then minimise console so camera window is front
time.sleep(0.6)
_minimize_console()

# ======================================================
# TIPS DATA  (drawn every frame on the right panel)
# ======================================================
_TIPS = [
    ("=== LEFT HAND — Keyboard ===", (0, 220, 255)),
    ("Hover 0.9s  : type the key",    (180, 180, 180)),
    ("SPACE key   : hover SPACE",     (180, 180, 180)),
    ("BACK key    : delete char",     (180, 180, 180)),
    ("CAPS key    : toggle uppercase",(180, 180, 180)),
    ("DRAW key    : toggle draw mode",(180, 180, 180)),
    ("Open palm (1.5s): draw mode",   (180, 180, 180)),
    ("CLR key     : clear drawing",   (180, 180, 180)),
    ("",                              (0,0,0)),
    ("=== RIGHT HAND — Mouse ===",    (0, 220, 255)),
    ("Index only  : move cursor",     (180, 180, 180)),
    ("Thumb+Index : LEFT CLICK",      (80, 255, 80)),
    ("Thumb+Middle: RIGHT CLICK",     (80, 200, 255)),
    ("3 fingers   : scroll up",       (255, 200, 0)),
    ("All 4 up    : scroll down",     (255, 140, 0)),
    ("Pinky only  : volume up/dn",    (255, 100, 200)),
    ("Fist        : brightness",      (200, 255, 80)),
    ("Idx+Mid     : screenshot",      (200, 100, 255)),
    ("Draw mode ON: pinch thumb+mid", (80, 100, 255)),
    ("",                              (0,0,0)),
    ('Say "STOP"  : end program',     (80, 100, 255)),
    ("ESC / Q     : end program",     (80, 100, 255)),
]

PANEL_X = DISPLAY_W - 310
PANEL_Y = 40
LINE_H  = 22


def _draw_tips(display):
    # Semi-transparent background
    ol = display.copy()
    cv2.rectangle(ol, (PANEL_X - 6, PANEL_Y - 4),
                  (DISPLAY_W - 2, PANEL_Y + len(_TIPS) * LINE_H + 4),
                  (12, 12, 18), -1)
    cv2.addWeighted(ol, 0.78, display, 0.22, 0, display)

    for i, (tip, col) in enumerate(_TIPS):
        if not tip:
            continue
        w_flag = 2 if tip.startswith("===") else 1
        cv2.putText(display, tip,
                    (PANEL_X, PANEL_Y + i * LINE_H + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, w_flag)


def _draw_header(display):
    cv2.rectangle(display, (0, 0), (DISPLAY_W, 38), (16, 16, 24), -1)
    # LEFT = keyboard
    cv2.putText(display, "LEFT HAND : KEYBOARD",
                (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 220, 255), 2)
    # divider
    cv2.line(display, (DISPLAY_W // 2, 2), (DISPLAY_W // 2, 36), (70, 70, 90), 1)
    # RIGHT = mouse
    cv2.putText(display, "RIGHT HAND : MOUSE",
                (DISPLAY_W // 2 + 10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (80, 255, 120), 2)


# ======================================================
# MAIN LOOP
# ======================================================
typed_text = ""

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
) as hands:

    cv2.namedWindow("Gesture Mouse + Keyboard", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Gesture Mouse + Keyboard", DISPLAY_W, DISPLAY_H)

    while not _stop_event.is_set():

        ret, frame = cap.read()
        if not ret:
            continue

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        # --- Resize raw camera frame to display resolution FIRST ---
        display = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

        # --- Apply shared canvas (drawing from either hand) ---
        shared_state.apply_canvas(display)

        # --- Header bar ---
        _draw_header(display)

        # --- Process each detected hand ---
        if result.multi_hand_landmarks and result.multi_handedness:
            for hand, side in zip(result.multi_hand_landmarks,
                                   result.multi_handedness):

                label = side.classification[0].label
                # After horizontal flip:
                #   MediaPipe "Right"  →  physical LEFT  hand  →  KEYBOARD
                #   MediaPipe "Left"   →  physical RIGHT hand  →  MOUSE
                if label == "Right":
                    char = code2_keyboard.process_hand(display, hand)
                    if char == "\b":
                        typed_text = typed_text[:-1]
                    elif char:
                        typed_text += char

                elif label == "Left":
                    code1_mouse.process_hand(display, hand)

                mp_draw.draw_landmarks(display, hand,
                                       mp_hands.HAND_CONNECTIONS,
                                       _lm_spec, _conn_spec)

        # --- Typed text bar (below header) ---
        if typed_text:
            cv2.rectangle(display, (0, 40), (PANEL_X - 10, 78), (8, 8, 14), -1)
            cv2.putText(display, f"Typed: {typed_text}",
                        (10, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)

        # --- Draw mode status strip ---
        if shared_state.draw_mode:
            cv2.rectangle(display, (0, DISPLAY_H - 30), (PANEL_X - 10, DISPLAY_H),
                          (0, 70, 0), -1)
            cv2.putText(display, "DRAW MODE ON  |  L-hand index draws  |  R-hand thumb+middle draws",
                        (8, DISPLAY_H - 9),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 120), 1)

        # --- Tips panel ---
        _draw_tips(display)

        # --- Show ---
        cv2.imshow("Gesture Mouse + Keyboard", display)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):   # Q or ESC
            _stop_event.set()

# ======================================================
# CLEANUP — restore console
# ======================================================
cap.release()
cv2.destroyAllWindows()
_restore_console()
print("\n[OK] Program stopped. Console restored.")
print("     Typed text was:", typed_text if typed_text else "(nothing typed)")