# AirSig - Enhanced Real-Time Finger Writing Application

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange.svg)

A robust, user-friendly real-time finger writing application using webcam, MediaPipe Hands, and OpenCV with a full Tkinter GUI.

## 🎯 Features

### Core Capabilities
- **Real-time Hand Tracking**: Uses MediaPipe Hands for accurate 21-landmark detection
- **Multiple Gestures**: 6+ gestures for drawing, navigation, erasing, and controls
- **Dual Hand Support**: Left hand for drawing, right hand for erasing
- **Temporal Smoothing**: 1€ filter implementation for smooth, jitter-free lines (latency <100ms)
- **Undo/Redo Stack**: 20-level undo/redo for drawings
- **Color Palette**: 8 colors (red, green, blue, yellow, cyan, magenta, white, black)
- **Adjustable Brush Size**: 1-20px with slider control
- **Export Options**: Save drawings as PNG/JPEG or record session as video (AVI/MP4)

### GUI Features
- **Modern Tkinter Interface**: 1000x700 resizable window
- **Control Panel**: Comprehensive left sidebar with all controls
- **Live Video Feed**: 640x480 embedded video with real-time overlay
- **Status Bar**: Shows current gesture, FPS counter, and instructions
- **Onboarding Tutorial**: Quick gesture guide popup on launch
- **Cross-Platform**: Works on Windows, Mac, and Linux

## 🎨 Gestures

| Gesture | Action | Description |
|---------|--------|-------------|
| ✏️ Index Finger Only | Draw | Point index finger to draw on canvas |
| 👆 Index + Middle | Navigate | Move cursor without drawing |
| 🖐️ All Fingers Extended | Erase | Erase drawings at fingertip |
| ✊ Fist (All Closed) | Clear All | Clear entire canvas |
| 🤚 Palm Open | Pause | Pause drawing activity |
| 🤏 Pinch (Thumb+Index) | Settings | Change color/size (visual indicator) |

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Webcam

### Install Dependencies

```bash
pip install opencv-python mediapipe numpy pillow
```

Or use requirements.txt:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Run the Application

```bash
python main.py
```

Or directly run the GUI:

```bash
python gui.py
```

### Using the App

1. **Start Webcam**: Click "Start Webcam" button in the control panel
2. **Draw**: Point your index finger and move to draw
3. **Navigate**: Extend index and middle fingers to move cursor without drawing
4. **Erase**: Extend all fingers to erase
5. **Clear**: Make a fist to clear the entire canvas
6. **Adjust Settings**: Use the control panel to change colors, brush size, etc.
7. **Export**: Save your drawing as an image or record the session as video

## 📁 Project Structure

```
AirSig/
├── main.py                    # Entry point
├── gui.py                     # Tkinter GUI application
├── hand_detector.py           # MediaPipe HandDetector class
├── utils.py                   # Utility functions (1€ filter, DrawingEngine, etc.)
├── Deploy.py                  # Original deployment script (legacy)
├── HandTracking_GestureRecognition_Module.py  # Original module (legacy)
├── Hand_Tracking.py           # Original hand tracking (legacy)
├── Gesture_Recognition.py     # Original gesture recognition (legacy)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── NavBar/                    # UI assets (optional)
    ├── Colors/
    ├── Homepage/
    └── Sizes/
```

## 🔧 Architecture

### Classes

#### `HandDetector` (hand_detector.py)
- MediaPipe Hands wrapper
- Supports dual hand detection
- Provides landmark extraction and finger state detection
- Methods: `find_hands()`, `find_positions()`, `get_all_hands()`, `get_finger_states()`

#### `DrawingEngine` (utils.py)
- Manages drawing canvas and masking
- Implements undo/redo stack (20 levels)
- Handles drawing, erasing, and overlay operations
- Methods: `draw_line()`, `erase()`, `overlay_on_frame()`, `undo()`, `redo()`, `clear()`

#### `GestureRecognizer` (utils.py)
- Enhanced gesture detection with 6+ gestures
- Uses gesture history for smoothing
- Supports handedness detection
- Methods: `recognize()`, returns gesture name and confidence

#### `OneEuroFilter` (utils.py)
- Temporal smoothing for fingertip trajectory
- Reduces jitter while maintaining low latency (<100ms)
- Configurable parameters: `min_cutoff`, `beta`, `d_cutoff`

#### `PointSmoother` (utils.py)
- Wrapper for 1€ filter for (x, y) coordinates
- Maintains separate filters for x and y
- Methods: `smooth()`, `reset()`

#### `ColorPalette` (utils.py)
- Predefined color palette (8 colors)
- BGR color format for OpenCV
- Methods: `get_color()`, `get_color_names()`

#### `AirSigGUI` (gui.py)
- Main Tkinter application
- Threaded video processing to prevent GUI freezing
- Integrates all components
- Handles user interactions and controls

## 🎛️ Configuration

### Smoothing Parameters
Edit in `utils.py` > `OneEuroFilter.__init__()`:
```python
min_cutoff = 1.0    # Lower = more smoothing
beta = 0.007        # Cutoff slope
d_cutoff = 1.0      # Derivative cutoff
```

### Hand Detection Settings
Edit in `gui.py` > `AirSigGUI.start_camera()`:
```python
detector = HandDetector(
    max_hands=2,           # Maximum hands to detect
    detection_con=0.7,     # Detection confidence threshold
    tracking_con=0.5       # Tracking confidence threshold
)
```

### Drawing Settings
Edit in `gui.py` > `AirSigGUI.__init__()`:
```python
self.brush_size = 5         # Default brush size (1-20)
self.eraser_size = 20       # Default eraser size
self.smoothing_enabled = True  # Enable/disable smoothing
```

## 🔬 Technical Details

### Temporal Smoothing
The application uses the **1€ (one-euro) filter** for temporal smoothing of fingertip coordinates. This filter:
- Reduces jitter and noise in hand tracking
- Maintains low latency (<100ms) for real-time interaction
- Adapts cutoff frequency based on signal velocity
- Provides smooth, natural-feeling cursor movement

### Drawing Overlay
Uses OpenCV masking and bitwise operations:
1. Convert canvas to grayscale
2. Apply threshold to create binary mask
3. Invert mask for transparency
4. Use `bitwise_and` and `bitwise_or` to overlay on video feed

### Threading
- Video processing runs in a separate daemon thread
- Thread lock (`threading.Lock()`) protects shared frame data
- Prevents GUI freezing during video processing

### Gesture Detection
- Uses finger tip positions relative to PIP joints
- Implements gesture history (5 frames) for stability
- Calculates distances for pinch detection
- Supports handedness (left/right) for different actions

## 🐛 Troubleshooting

### Camera Not Opening
- Check camera permissions
- Try changing camera index: `cv2.VideoCapture(1)` instead of `cv2.VideoCapture(0)`
- Ensure no other application is using the camera

### Poor Hand Detection
- Ensure good lighting
- Adjust detection confidence: `detection_con=0.5` (lower = more sensitive)
- Keep hands within camera frame
- Avoid busy backgrounds

### Lag or Low FPS
- Close other applications
- Reduce camera resolution in `start_camera()`: `cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)`
- Disable landmark drawing: Uncheck "Show Landmarks"
- Disable smoothing if needed

### Import Errors
```bash
pip install --upgrade opencv-python mediapipe numpy pillow
```

## 📊 Performance

- **FPS**: 20-30 FPS on standard laptop webcam
- **Latency**: <100ms with smoothing enabled
- **Hand Detection**: Up to 2 hands simultaneously
- **Undo Stack**: 20 levels (configurable)

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional gestures (peace sign, thumbs up, etc.)
- ML-based gesture classification
- Multi-color gradient drawing
- Shape detection and auto-correction
- Cloud storage integration
- Mobile app version

## 📝 License

This project is open source. Feel free to use, modify, and distribute.

## 👏 Acknowledgments

- **MediaPipe**: Google's MediaPipe Hands for hand tracking
- **OpenCV**: Computer vision library
- **1€ Filter**: Géry Casiez, Nicolas Roussel, and Daniel Vogel for the filter algorithm

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Enjoy drawing with your fingers! ✨**
