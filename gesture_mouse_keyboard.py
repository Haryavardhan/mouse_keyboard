import cv2
import mediapipe as mp
import time

import code1_mouse
import code2_keyboard

print("Starting Gesture Mouse + Keyboard")

# ===== CAMERA =====
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

time.sleep(2)

if not cap.isOpened():
    print("❌ Camera not opened")
    exit()

print("✅ Camera opened successfully")

# ===== MEDIAPIPE =====
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# 🔥 IMPORTANT FIX (use WITH)
with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as hands:

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Frame read failed")
            continue

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb)

        if results.multi_hand_landmarks:

            for i, hand in enumerate(results.multi_hand_landmarks):

                # 👉 FIRST HAND → MOUSE
                if i == 0:
                    code1_mouse.process_hand(frame, hand)

                # 👉 SECOND HAND → KEYBOARD
                if i == 1:
                    code2_keyboard.process_hand(frame, hand)

                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Gesture Mouse + Keyboard", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# ===== CLEANUP =====
cap.release()
cv2.destroyAllWindows()
print("Program closed")