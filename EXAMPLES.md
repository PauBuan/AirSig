# 🎨 AirSig Usage Examples

## Basic Usage

### Starting the Application

```bash
# Method 1: Using main entry point
python main.py

# Method 2: Directly running GUI
python gui.py
```

---

## 📝 Common Workflows

### Workflow 1: Simple Drawing Session

1. **Launch** the application
   ```bash
   python main.py
   ```

2. **Start webcam**
   - Click "Start Webcam" button in control panel
   - Wait for video feed to appear

3. **Draw**
   - Point index finger only
   - Move finger to draw
   - Default color: Red, size: 5px

4. **Stop**
   - Click "Stop Webcam"
   - Or close the window

### Workflow 2: Multi-Color Drawing

1. **Start webcam**

2. **Select first color**
   - Use color dropdown → Select "red"
   - Draw with index finger

3. **Change color**
   - Use color dropdown → Select "blue"
   - Draw more

4. **Save your work**
   - Click "Save Image"
   - Choose location and filename
   - Done!

### Workflow 3: Recording a Session

1. **Start webcam**

2. **Click "Start Recording"**
   - Record button changes to "Stop Recording"
   - Status shows recording active

3. **Draw your content**
   - Use gestures as normal
   - All actions are recorded

4. **Click "Stop Recording"**
   - Choose save location
   - Video saved as AVI/MP4

### Workflow 4: Using Advanced Gestures

1. **Start webcam**

2. **Draw** (Index finger only)
   - Point index finger
   - Move to draw

3. **Navigate** (Index + Middle)
   - Extend index and middle fingers
   - Move cursor without drawing
   - Use to position for next stroke

4. **Erase** (All fingers)
   - Extend all fingers (index, middle, ring, pinky)
   - Move over areas to erase

5. **Clear all** (Fist)
   - Make a fist (all fingers closed)
   - Canvas clears completely

6. **Pause** (Palm open)
   - Open all fingers wide
   - Pauses drawing temporarily

### Workflow 5: Using Undo/Redo

1. **Draw something**
   - Make several strokes

2. **Made a mistake?**
   - Click "Undo" button
   - Last stroke removed
   - Can undo up to 20 times

3. **Changed your mind?**
   - Click "Redo" button
   - Stroke comes back

4. **Continue drawing**
   - Redo stack clears when new action taken

---

## ⚙️ Advanced Features

### Custom Brush Sizes

```python
# In GUI:
1. Move "Brush Size" slider
2. See size update in real-time (1-20px)
3. Eraser automatically becomes 3x brush size
```

### Enabling/Disabling Smoothing

```python
# In GUI:
1. Check/uncheck "Enable Smoothing"
2. Smoothing uses 1€ filter for jitter reduction
3. Disable for lower latency (but more jitter)
```

### Showing/Hiding Hand Landmarks

```python
# In GUI:
1. Check/uncheck "Show Landmarks"
2. Shows MediaPipe hand skeleton
3. Useful for debugging gesture detection
```

---

## 🎯 Gesture Examples

### Drawing a Circle

1. Start webcam
2. Point index finger only
3. Move finger in circular motion
4. Smooth circle appears on canvas

### Writing Your Name

1. Start webcam
2. Select preferred color (e.g., blue)
3. Adjust brush size if needed (e.g., 3px for fine writing)
4. Point index finger
5. Write each letter
6. Use index+middle to move between letters without drawing

### Creating Art with Multiple Colors

1. Start webcam
2. Draw outline in black
   - Select "black" from dropdown
   - Draw with index finger
3. Fill with red
   - Select "red"
   - Increase brush size to 15px
   - Fill areas
4. Add blue accents
   - Select "blue"
   - Decrease brush size to 3px
   - Add details
5. Save image

### Erasing Mistakes

1. Drew something wrong?
2. Extend all 4 fingers (index, middle, ring, pinky)
3. Move over the mistake
4. Mistake erased!

Alternative:
- Click "Undo" button to remove last action

### Quick Canvas Clear

1. Want to start over?
2. Make a fist (close all fingers)
3. Canvas instantly clears

Alternative:
- Click "Clear Canvas" button

---

## 💡 Pro Tips

### Tip 1: Smooth Lines
```
Enable "Enable Smoothing" checkbox for smoother, less jittery lines.
Trade-off: Slight latency (~50-80ms) but much smoother appearance.
```

### Tip 2: Fine Detail Work
```
1. Reduce brush size to 1-3px
2. Enable smoothing
3. Move finger slowly for precision
4. Use good lighting for better hand detection
```

### Tip 3: Quick Navigation
```
Use Index+Middle gesture to move between areas without drawing.
Faster than lifting hand out of frame!
```

### Tip 4: Layered Drawing
```
1. Draw base layer in one color
2. Use undo if mistakes
3. Change color
4. Add details on top
5. Undo individual strokes if needed (20 levels!)
```

### Tip 5: Recording Presentations
```
1. Start recording before drawing
2. Draw and explain simultaneously
3. Use gestures (fist to clear, etc.)
4. Stop recording
5. Share video of your presentation!
```

---

## 🔧 Customization Examples

### Changing Default Settings (in code)

#### Default Brush Size
```python
# In gui.py, line ~60
self.brush_size = 10  # Change from 5 to 10
```

#### Default Color
```python
# In gui.py, line ~58
self.brush_color = ColorPalette.get_color('blue')  # Instead of red
```

#### Undo Stack Size
```python
# In utils.py, DrawingEngine class
self.undo_stack = deque(maxlen=50)  # Change from 20 to 50
```

#### Smoothing Parameters
```python
# In utils.py, OneEuroFilter class
def __init__(self, min_cutoff=2.0, beta=0.01, d_cutoff=1.5):
    # Experiment with different values:
    # - Higher min_cutoff = less smoothing
    # - Higher beta = more responsive to speed
```

#### Camera Resolution
```python
# In gui.py, start_camera() method
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Higher resolution
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

### Adding New Colors

```python
# In utils.py, ColorPalette class
COLORS = {
    'red': (0, 0, 255),
    'green': (0, 255, 0),
    'blue': (255, 0, 0),
    # Add new colors:
    'orange': (0, 165, 255),
    'purple': (255, 0, 128),
    'brown': (42, 42, 165)
}
```

Then update GUI dropdown in `gui.py`:
```python
# Color picker will automatically include new colors
# from ColorPalette.get_color_names()
```

---

## 🐛 Troubleshooting Examples

### Problem: Gesture not detected

**Solution:**
```python
# Lower detection confidence
# In gui.py, line ~226
detector = HandDetector(max_hands=2, detection_con=0.5)  # Lower from 0.7
```

### Problem: Too much smoothing lag

**Solution:**
```python
# Adjust 1€ filter parameters in utils.py
OneEuroFilter(min_cutoff=2.0, beta=0.01)  # Higher cutoff = less smoothing
```

Or disable smoothing:
```
Uncheck "Enable Smoothing" in GUI
```

### Problem: Lines too thick

**Solution:**
```
Move "Brush Size" slider to left (minimum 1px)
```

### Problem: Camera shows wrong view

**Solution:**
```python
# Try different camera index in gui.py
self.cap = cv2.VideoCapture(1)  # Change from 0 to 1
```

---

## 📊 Performance Optimization Examples

### For Better FPS

1. **Disable landmarks**
   - Uncheck "Show Landmarks"

2. **Lower resolution**
   ```python
   # In gui.py
   self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
   self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
   ```

3. **Disable smoothing**
   - Uncheck "Enable Smoothing"

4. **Reduce max hands**
   ```python
   # In gui.py
   detector = HandDetector(max_hands=1)  # Only detect one hand
   ```

### For Better Accuracy

1. **Increase detection confidence**
   ```python
   detector = HandDetector(detection_con=0.8, tracking_con=0.7)
   ```

2. **Enable gesture history smoothing** (already enabled)
   ```python
   # In utils.py, GestureRecognizer
   self.gesture_history = deque(maxlen=10)  # Increase from 5
   ```

---

## 🎓 Educational Examples

### Example 1: Teaching Math

```
1. Start AirSig
2. Draw equation in blue
3. Show steps in red
4. Highlight answer in green
5. Record entire session
6. Share with students
```

### Example 2: Art Tutorial

```
1. Start recording
2. Draw basic shapes in black
3. Explain while drawing
4. Add colors and details
5. Use fist gesture to clear and start over if needed
6. Save final artwork as image
```

### Example 3: Gesture Research

```
1. Enable "Show Landmarks"
2. Observe hand skeleton
3. Test different gestures
4. Record for analysis
5. Export frames for documentation
```

---

## 🚀 Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│             GESTURE QUICK REFERENCE              │
├─────────────────────────────────────────────────┤
│ ✏️  Index Only        → Draw                    │
│ 👆 Index + Middle     → Navigate                │
│ 🖐️  All Fingers       → Erase                  │
│ ✊  Fist               → Clear Canvas            │
│ 🤚  Palm Open          → Pause                  │
│ 🤏  Pinch              → Settings               │
├─────────────────────────────────────────────────┤
│             BUTTON QUICK REFERENCE               │
├─────────────────────────────────────────────────┤
│ Start Webcam          → Begin tracking          │
│ Stop Webcam           → End session             │
│ Clear Canvas          → Remove all drawings     │
│ Undo                  → Remove last action      │
│ Redo                  → Restore last undo       │
│ Save Image            → Export as PNG/JPG       │
│ Start/Stop Recording  → Record video            │
├─────────────────────────────────────────────────┤
│             SETTINGS QUICK REFERENCE             │
├─────────────────────────────────────────────────┤
│ Color Dropdown        → 8 colors                │
│ Brush Size Slider     → 1-20px                  │
│ Enable Smoothing      → Toggle 1€ filter        │
│ Show Landmarks        → Toggle hand skeleton    │
└─────────────────────────────────────────────────┘
```

---

**Happy Drawing! 🎨✨**

For more help, see:
- README_ENHANCED.md - Complete documentation
- QUICKSTART.md - Getting started guide
- ARCHITECTURE.md - Technical details
