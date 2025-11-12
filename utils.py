"""
Utility functions for AirSig - Enhanced finger writing application
Includes 1€ Filter for temporal smoothing and drawing utilities
"""

import cv2
import numpy as np
import time
from collections import deque


class OneEuroFilter:
    """
    1€ Filter for temporal smoothing of fingertip trajectory
    Reduces jitter while maintaining low latency (<100ms)
    """
    def __init__(self, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def __call__(self, x, t=None):
        """Apply filter to new value x at time t"""
        if t is None:
            t = time.time()
        
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x
        
        # Calculate time difference
        dt = t - self.t_prev
        if dt <= 0:
            dt = 0.001  # Prevent division by zero
        
        # Calculate derivative
        dx = (x - self.x_prev) / dt
        
        # Smooth derivative
        edx = self._smooth(dx, self.dx_prev, self._alpha(dt, self.d_cutoff))
        
        # Smooth value
        cutoff = self.min_cutoff + self.beta * abs(edx)
        x_filtered = self._smooth(x, self.x_prev, self._alpha(dt, cutoff))
        
        # Update state
        self.x_prev = x_filtered
        self.dx_prev = edx
        self.t_prev = t
        
        return x_filtered
    
    def _alpha(self, dt, cutoff):
        """Calculate alpha parameter"""
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
    
    def _smooth(self, x, x_prev, alpha):
        """Apply exponential smoothing"""
        return alpha * x + (1 - alpha) * x_prev


class PointSmoother:
    """Smooth (x, y) coordinates using 1€ filters"""
    def __init__(self):
        self.filter_x = OneEuroFilter()
        self.filter_y = OneEuroFilter()
    
    def smooth(self, point, t=None):
        """Smooth a (x, y) point"""
        if point is None:
            return None
        x, y = point
        x_smooth = self.filter_x(x, t)
        y_smooth = self.filter_y(y, t)
        return (int(x_smooth), int(y_smooth))
    
    def reset(self):
        """Reset filter state"""
        self.filter_x = OneEuroFilter()
        self.filter_y = OneEuroFilter()


class DrawingEngine:
    """
    Manages drawing canvas, masking, and bitwise operations
    Handles undo/redo stack and drawing operations
    """
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype='uint8')
        self.undo_stack = deque(maxlen=20)  # Store last 20 states
        self.redo_stack = deque(maxlen=20)
        self.save_state()
    
    def save_state(self):
        """Save current canvas state to undo stack"""
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()  # Clear redo when new action is taken
    
    def undo(self):
        """Undo last drawing action"""
        if len(self.undo_stack) > 1:  # Keep at least one state
            self.redo_stack.append(self.undo_stack.pop())
            self.canvas = self.undo_stack[-1].copy()
            return True
        return False
    
    def redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.canvas = state.copy()
            return True
        return False
    
    def clear(self):
        """Clear the canvas"""
        self.save_state()
        self.canvas = np.zeros((self.height, self.width, 3), dtype='uint8')
    
    def draw_line(self, pt1, pt2, color, thickness):
        """Draw a line on canvas"""
        if pt1 and pt2:
            cv2.line(self.canvas, pt1, pt2, color, thickness)
    
    def erase(self, center, radius):
        """Erase at given position"""
        if center:
            cv2.circle(self.canvas, center, radius, (0, 0, 0), -1)
    
    def overlay_on_frame(self, frame):
        """Overlay canvas on video frame using masking"""
        # Convert canvas to grayscale for masking
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        
        # Combine frame and canvas
        frame = cv2.bitwise_and(frame, img_inv)
        frame = cv2.bitwise_or(frame, self.canvas)
        return frame
    
    def get_canvas(self):
        """Get current canvas"""
        return self.canvas.copy()
    
    def resize(self, width, height):
        """Resize canvas (for window resize)"""
        self.canvas = cv2.resize(self.canvas, (width, height))
        self.width = width
        self.height = height


class GestureRecognizer:
    """
    Enhanced gesture recognition with multiple gestures
    Gestures: Index (draw), Index+Middle (navigate), All fingers (erase),
              Palm open (pause), Fist (clear), Pinch (change color/size)
    """
    def __init__(self):
        self.gesture_history = deque(maxlen=5)  # Smooth gesture detection
        self.current_gesture = "none"
    
    def recognize(self, landmarks, handedness=None):
        """
        Recognize gesture from hand landmarks
        Returns: gesture name and confidence
        """
        if not landmarks or len(landmarks) < 21:
            return "none", 0.0
        
        # Get finger states
        fingers = self._get_finger_states(landmarks)
        thumb, index, middle, ring, pinky = fingers
        
        # Calculate distances for pinch detection
        thumb_index_dist = self._distance(landmarks[4], landmarks[8])
        
        # Recognize gestures
        gesture = "none"
        confidence = 1.0
        
        # Fist - all fingers closed
        if sum(fingers) == 0:
            gesture = "fist"
        
        # Palm open - all fingers extended
        elif sum(fingers) == 5:
            gesture = "palm_open"
        
        # Pinch - thumb and index close together
        elif thumb_index_dist < 40:
            gesture = "pinch"
        
        # Index finger only - drawing
        elif index and not middle and not ring and not pinky:
            gesture = "draw"
        
        # Index + Middle - navigation/move
        elif index and middle and not ring and not pinky:
            gesture = "navigate"
        
        # Four fingers (no thumb) - erasing
        elif index and middle and ring and pinky:
            gesture = "erase"
        
        # Add to history for smoothing
        self.gesture_history.append(gesture)
        
        # Use most common gesture in history
        if self.gesture_history:
            gesture = max(set(self.gesture_history), key=self.gesture_history.count)
        
        self.current_gesture = gesture
        return gesture, confidence
    
    def _get_finger_states(self, landmarks):
        """
        Determine which fingers are extended
        Returns: [thumb, index, middle, ring, pinky]
        """
        fingers = []
        
        # Thumb - check x coordinate (different for left/right hand)
        if landmarks[4][1] < landmarks[3][1]:  # Simplified thumb check
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers - check y coordinate (tip vs pip joint)
        finger_tips = [8, 12, 16, 20]
        for tip_id in finger_tips:
            if landmarks[tip_id][2] < landmarks[tip_id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def _distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)


class ColorPalette:
    """Color palette for drawing"""
    COLORS = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'cyan': (255, 255, 0),
        'magenta': (255, 0, 255),
        'white': (255, 255, 255),
        'black': (0, 0, 0)
    }
    
    @classmethod
    def get_color(cls, name):
        """Get color by name"""
        return cls.COLORS.get(name.lower(), (255, 255, 255))
    
    @classmethod
    def get_color_names(cls):
        """Get list of available color names"""
        return list(cls.COLORS.keys())


def calculate_fps(prev_time):
    """Calculate FPS"""
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if curr_time > prev_time else 0
    return fps, curr_time


def draw_landmarks_on_frame(frame, landmarks, connections=None):
    """Draw hand landmarks on frame"""
    if not landmarks:
        return frame
    
    # Draw landmarks
    for lm in landmarks:
        x, y = lm[1], lm[2]
        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
    
    return frame
