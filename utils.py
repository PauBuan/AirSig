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
    Enhanced parameters for smoother drawing
    """
    def __init__(self, min_cutoff=0.5, beta=0.005, d_cutoff=1.0):
        self.min_cutoff = min_cutoff  # Reduced from 1.0 to 0.5 for more smoothing
        self.beta = beta  # Reduced from 0.007 to 0.005 for less jitter
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
    """Smooth (x, y) coordinates using 1€ filters with moving average and jitter reduction"""
    def __init__(self, window_size=3, jitter_threshold=5, stabilization='high'):
        self.window_size = window_size
        self.jitter_threshold = jitter_threshold
        self.stabilization = stabilization
        
        # Adjust filter parameters based on stabilization level
        if stabilization == 'low':
            self.filter_x = OneEuroFilter(min_cutoff=1.0, beta=0.01)
            self.filter_y = OneEuroFilter(min_cutoff=1.0, beta=0.01)
            self.window_size = 2
        elif stabilization == 'medium':
            self.filter_x = OneEuroFilter(min_cutoff=0.5, beta=0.005)
            self.filter_y = OneEuroFilter(min_cutoff=0.5, beta=0.005)
            self.window_size = 3
        else:  # high
            self.filter_x = OneEuroFilter(min_cutoff=0.3, beta=0.003)
            self.filter_y = OneEuroFilter(min_cutoff=0.3, beta=0.003)
            self.window_size = 5
        
        self.point_history = deque(maxlen=self.window_size)
        self.last_stable_point = None
    
    def smooth(self, point, t=None):
        """Smooth a (x, y) point with 1€ filter + moving average + jitter reduction"""
        if point is None:
            return None
        x, y = point
        
        # Jitter reduction: ignore small movements
        if self.last_stable_point:
            dx = abs(x - self.last_stable_point[0])
            dy = abs(y - self.last_stable_point[1])
            if dx < self.jitter_threshold and dy < self.jitter_threshold:
                # Movement too small, keep last position (reduces jitter)
                return self.last_stable_point
        
        # Apply 1€ filter first
        x_smooth = self.filter_x(x, t)
        y_smooth = self.filter_y(y, t)
        
        # Add to history
        self.point_history.append((x_smooth, y_smooth))
        
        # Apply moving average
        if len(self.point_history) > 0:
            avg_x = sum(p[0] for p in self.point_history) / len(self.point_history)
            avg_y = sum(p[1] for p in self.point_history) / len(self.point_history)
            result = (int(avg_x), int(avg_y))
        else:
            result = (int(x_smooth), int(y_smooth))
        
        self.last_stable_point = result
        return result
    
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
        self.canvas = np.full((height, width, 3), 255, dtype='uint8')  # White background
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
        self.canvas = np.full((self.height, self.width, 3), 255, dtype='uint8')  # White background
    
    def draw_line(self, pt1, pt2, color, thickness):
        """Draw a smooth anti-aliased line on canvas with interpolation for large gaps"""
        if pt1 and pt2:
            # Calculate distance between points
            dist = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
            
            # If points are far apart, interpolate to avoid gaps
            if dist > thickness * 2:
                # Calculate number of intermediate points
                num_points = int(dist / (thickness / 2))
                for i in range(num_points):
                    t = i / num_points
                    x = int(pt1[0] + t * (pt2[0] - pt1[0]))
                    y = int(pt1[1] + t * (pt2[1] - pt1[1]))
                    cv2.circle(self.canvas, (x, y), thickness // 2, color, -1, cv2.LINE_AA)
            
            # Draw the main line with anti-aliasing
            cv2.line(self.canvas, pt1, pt2, color, thickness, cv2.LINE_AA)
    
    def erase(self, center, radius):
        """Erase at given position with smooth edges"""
        if center:
            # Use anti-aliased circle for smoother erasing (erase to white)
            cv2.circle(self.canvas, center, radius, (255, 255, 255), -1, cv2.LINE_AA)
    
    def overlay_on_frame(self, frame):
        """Overlay canvas onto video frame"""
        # Ensure canvas and frame have the same dimensions
        if frame.shape != self.canvas.shape:
            canvas_resized = cv2.resize(self.canvas, (frame.shape[1], frame.shape[0]))
        else:
            canvas_resized = self.canvas
        
        # Convert canvas to grayscale for masking
        gray = cv2.cvtColor(canvas_resized, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        
        # Combine frame and canvas
        frame = cv2.bitwise_and(frame, img_inv)
        frame = cv2.bitwise_or(frame, canvas_resized)
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
        
        # Palm open - all fingers extended (including thumb)
        elif sum(fingers) == 5:
            gesture = "palm_open"
        
        # Erase - thumb closed + 4 fingers extended (index, middle, ring, pinky)
        elif not thumb and index and middle and ring and pinky:
            gesture = "erase"
        
        # Pinch - thumb and index close together
        elif thumb_index_dist < 40:
            gesture = "pinch"
        
        # Index finger only - drawing
        elif index and not middle and not ring and not pinky:
            gesture = "draw"
        
        # Index + Middle - navigation/move
        elif index and middle and not ring and not pinky:
            gesture = "navigate"
        
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
        Works consistently for both left and right hands
        """
        fingers = []
        
        # Thumb - check if tip is farther from wrist than IP joint
        # Using distance from wrist (landmark 0) for consistent detection
        thumb_tip_dist = self._distance(landmarks[0], landmarks[4])
        thumb_ip_dist = self._distance(landmarks[0], landmarks[3])
        
        if thumb_tip_dist > thumb_ip_dist:
            fingers.append(1)  # Thumb extended
        else:
            fingers.append(0)  # Thumb closed
        
        # Other fingers - check y coordinate (tip vs pip joint)
        # Tip should be higher (smaller y) than PIP joint when extended
        finger_tips = [8, 12, 16, 20]
        for tip_id in finger_tips:
            if landmarks[tip_id][2] < landmarks[tip_id - 2][2]:
                fingers.append(1)  # Finger extended
            else:
                fingers.append(0)  # Finger closed
        
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
    """Calculate FPS with division by zero protection"""
    curr_time = time.time()
    time_diff = curr_time - prev_time
    fps = 1 / time_diff if time_diff > 0.001 else 0  # Prevent division by zero
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
