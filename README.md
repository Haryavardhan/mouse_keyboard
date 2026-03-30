# 🖱️ Virtual Gesture Mouse + Keyboard

Control your PC using **hand gestures** detected via webcam — no touch, no extra hardware.

- **Left Hand** → Virtual Keyboard (hover to type)
- **Right Hand** → Mouse control (move, click, scroll, volume, brightness, screenshot)
- **Both hands together** → Draw on screen

---

## 🖥️ Demo

| Hand | Mode | Gesture |
|------|------|---------|
| Left | Keyboard | Hover index finger over a key for **0.9 s** to type it |
| Left | Draw | Open palm (hold 1.5 s) OR hover **DRAW** key |
| Right | Move cursor | Raise **index finger only** |
| Right | Left Click | **Thumb + Index** pinch (close together) |
| Right | Right Click | **Thumb + Middle** pinch |
| Right | Scroll Up | Index + Middle + Ring fingers up |
| Right | Scroll Down | All 4 fingers up |
| Right | Volume | Pinky only up → thumb up = Vol+, thumb down = Vol− |
| Right | Brightness | Fist (no fingers) → thumb up = Bright+, thumb down = Bright− |
| Right | Screenshot | Index + Middle up (2-finger peace sign) |
| Right | Draw | In draw mode: pinch **Thumb + Middle** to draw (blue) |

---

## ⚙️ Setup

### 1. Clone the repository
```bash
git clone https://github.com/Haryavardhan/mouse_keyboard.git
cd mouse_keyboard
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Windows PyAudio note:** If `pip install pyaudio` fails, use:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 4. Run the program
```bash
python gesture_mouse_keyboard.py
```

The console window will **auto-minimise** and the camera window will appear.

---

## 🛑 Stopping the Program

| Method | How |
|--------|-----|
| Voice | Say **"stop"** into the microphone |
| Keyboard | Press **Q** or **ESC** in the camera window |

The console is automatically restored when the program stops.

---

## 📁 File Structure

```
mouse_keyboard/
├── gesture_mouse_keyboard.py   # Main entry point
├── code1_mouse.py              # Right hand — mouse control
├── code2_keyboard.py           # Left hand  — virtual keyboard
├── shared_state.py             # Shared canvas / draw-mode flag
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🐍 Requirements

- Python **3.9 – 3.11** (MediaPipe does not support 3.12+ yet)
- Webcam
- Windows 10/11 (tested)

---

## 🙌 Credits

Built with:
- [MediaPipe](https://mediapipe.dev/) — hand landmark detection
- [OpenCV](https://opencv.org/) — camera & drawing
- [PyAutoGUI](https://pyautogui.readthedocs.io/) — mouse & keyboard automation
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) — voice stop command
