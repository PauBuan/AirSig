# AirSig - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies
Open PowerShell/Command Prompt and run:

```powershell
pip install opencv-python mediapipe numpy pillow
```

Or use the requirements file:

```powershell
cd "c:\Users\Paulo\Documents\MCL DOCS2\4th year\Image proc\Finals\Finger Writing\AirSig\AirSig"
pip install -r requirements.txt
```

### Step 2: Run the Application

```powershell
python main.py
```

### Step 3: Start Drawing!

1. Click **"Start Webcam"** button
2. Point your **index finger** at the camera to draw
3. Use the control panel to change colors and brush size
4. Have fun! ✨

---

## 📋 File Structure

### New Enhanced Files:
- **main.py** - Entry point to launch the application
- **gui.py** - Full Tkinter GUI with all controls
- **hand_detector.py** - Enhanced HandDetector class
- **utils.py** - Utility functions (1€ filter, DrawingEngine, GestureRecognizer)
- **requirements.txt** - Python dependencies
- **README_ENHANCED.md** - Complete documentation

### Legacy Files (kept for reference):
- Deploy.py
- HandTracking_GestureRecognition_Module.py
- Hand_Tracking.py
- Gesture_Recognition.py

---

## 🎨 Gesture Cheat Sheet

```
✏️  INDEX FINGER ONLY        → Draw on canvas
👆  INDEX + MIDDLE FINGERS   → Navigate/Move cursor  
🖐️  ALL FINGERS EXTENDED     → Erase
✊  FIST (ALL CLOSED)        → Clear entire canvas
🤚  PALM OPEN                → Pause drawing
🤏  PINCH (THUMB + INDEX)    → Change settings indicator
```

---

## ⚙️ Key Features Implemented

### ✅ Core Improvements:
- [x] 1€ Filter for temporal smoothing (reduce jitter, <100ms latency)
- [x] Enhanced gesture detection (6+ gestures)
- [x] Color palette with 8 colors (red, blue, green, yellow, cyan, magenta, white, black)
- [x] Brush size slider (1-20px)
- [x] Undo/Redo stack (20 levels)
- [x] Dual hand support (left for drawing, right for erasing)
- [x] Export drawing as PNG/JPEG
- [x] Record session as AVI/MP4 video

### ✅ GUI Features:
- [x] Full Tkinter GUI (1000x700, resizable)
- [x] Left control panel with all settings
- [x] Embedded video feed (640x480, auto-resizes)
- [x] Status bar with gesture label, FPS counter, instructions
- [x] Onboarding popup tutorial
- [x] Cross-platform support (Windows/Mac/Linux)

### ✅ Code Restructuring:
- [x] HandDetector class (MediaPipe wrapper)
- [x] GestureRecognizer class (enhanced gesture detection)
- [x] DrawingEngine class (canvas, masking, undo/redo)
- [x] Video processing in separate thread (prevents GUI freezing)
- [x] Modular, clean, well-commented code

---

## 🎯 Controls Overview

### Camera Controls:
- **Start Webcam** - Initialize camera and start tracking
- **Stop Webcam** - Stop camera and release resources

### Drawing Controls:
- **Clear Canvas** - Clear all drawings
- **Undo** - Undo last drawing action (20 levels)
- **Redo** - Redo last undone action

### Settings:
- **Color Dropdown** - Select drawing color (8 colors)
- **Brush Size Slider** - Adjust brush size (1-20px)
- **Enable Smoothing** - Toggle 1€ filter smoothing
- **Show Landmarks** - Toggle hand landmark visualization

### Export:
- **Save Image** - Export canvas as PNG/JPEG
- **Start/Stop Recording** - Record video session

---

## 🔧 Troubleshooting

### Problem: Camera won't open
**Solution:** 
- Check camera permissions in Windows Settings
- Make sure no other app is using the camera
- Try changing camera index in `gui.py` line 228: `cv2.VideoCapture(1)`

### Problem: Hand detection not working
**Solution:**
- Ensure good lighting
- Keep hands within camera frame
- Adjust detection confidence in `gui.py` line 226: `detection_con=0.5` (lower = more sensitive)

### Problem: Low FPS / Lag
**Solution:**
- Disable "Show Landmarks" checkbox
- Reduce camera resolution
- Close other applications

### Problem: Import errors
**Solution:**
```powershell
pip install --upgrade opencv-python mediapipe numpy pillow
```

---

## 💡 Tips for Best Results

1. **Lighting**: Use good, even lighting for better hand detection
2. **Background**: Plain, solid-color backgrounds work best
3. **Distance**: Keep hands 1-2 feet from camera
4. **Gestures**: Make clear, distinct gestures
5. **Smoothing**: Enable smoothing for smoother lines
6. **Practice**: Try the onboarding tutorial gestures

---

## 📊 Performance Expectations

- **FPS**: 20-30 FPS (typical laptop webcam)
- **Latency**: <100ms with smoothing enabled
- **Hands**: Detects up to 2 hands simultaneously
- **Gestures**: 6+ gesture types supported
- **Undo Levels**: 20 states saved

---

## 🎓 Next Steps

1. **Experiment** with different colors and brush sizes
2. **Try dual hands** - left for drawing, right for erasing
3. **Record a session** and save as video
4. **Export your artwork** as an image
5. **Customize** the code to add your own gestures!

---

## 📞 Need Help?

- Check **README_ENHANCED.md** for detailed documentation
- Review code comments in each file
- Open an issue on GitHub

**Happy Drawing! 🎨✨**
