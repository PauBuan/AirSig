"""
AirSig - Enhanced Real-Time Finger Writing Application
Full Tkinter GUI with video processing in separate thread
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np
from datetime import datetime
import os

# Import custom modules
from hand_detector import HandDetector
from utils import (
    DrawingEngine, GestureRecognizer, ColorPalette, 
    PointSmoother, calculate_fps, draw_landmarks_on_frame
)


class AirSigGUI:
    """
    Main GUI application for AirSig finger writing
    """
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("AirSig - Real-Time Finger Writing")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Application state
        self.running = False
        self.camera_active = False
        self.cap = None
        self.current_frame = None
        
        # Drawing settings
        self.brush_color = (0, 0, 255)  # Red (BGR)
        self.brush_size = 5
        self.brush_opacity = 1.0  # New: Brush opacity (0.0 to 1.0)
        self.brush_style = 'normal'  # New: Brush style (normal, marker, spray)
        self.pressure_enabled = False  # New: Pressure simulation based on hand distance
        self.eraser_size = 20
        self.smoothing_enabled = True
        self.show_landmarks = True
        
        # Color cycling for pinch gesture
        self.color_list = ['red', 'blue', 'green', 'yellow', 'cyan', 'magenta', 'white', 'black']
        self.current_color_index = 0
        self.last_pinch_state = False  # Track pinch state to detect transitions
        
        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_interval = 60  # seconds
        self.last_auto_save = time.time()
        self.current_project_path = None
        self.project_modified = False
        
        # Canvas enhancement settings
        self.show_grid = False
        self.show_rulers = False
        self.canvas_zoom = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self.grid_size = 50
        
        # Two-hand gesture state
        self.two_hand_mode = None
        self.last_two_hand_distance = None
        
        # Hand stabilization settings
        self.stabilization_level = 'high'  # 'low', 'medium', 'high'
        self.jitter_threshold = 5  # pixels
        
        # Camera settings
        self.camera_index = 0
        self.available_cameras = []
        self.low_light_mode = False
        self.brightness_adjustment = 10
        self.contrast_adjustment = 1.1
        
        # UI Theme
        self.current_theme = 'light'  # 'light', 'dark'
        self.ui_scale = 1.0
        
        # Components
        self.detector = None
        self.drawing_engine = None
        self.gesture_recognizer = None
        self.smoothers = {}  # Smoother for each hand
        
        # Video processing thread
        self.video_thread = None
        self.thread_lock = threading.Lock()
        
        # Gesture state
        self.current_gesture = "none"
        self.prev_draw_point = None
        self.fps = 0
        
        # Recording
        self.recording = False
        self.recording_paused = False  # New: Pause/resume recording
        self.video_writer = None
        self.recorded_frames = []
        self.recording_start_time = None
        self.recording_timestamps = []  # New: Store timestamp markers
        
        # Shape tool state
        self.shape_mode = None  # None, 'circle', 'rectangle', 'arrow', 'line'
        self.shape_start_point = None
        self.temp_shape = None
        
        # Setup GUI
        self.setup_gui()
        
        # Show onboarding
        self.show_onboarding()
    
    def setup_gui(self):
        """Setup GUI components"""
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Left panel - Controls
        self.setup_control_panel()
        
        # Right panel - Video feed
        self.setup_video_panel()
        
        # Bottom status bar
        self.setup_status_bar()
    
    def setup_control_panel(self):
        """Setup left control panel with scrollbar"""
        # Create main container frame
        container = ttk.Frame(self.root, padding="5")
        container.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), padx=5, pady=5)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(container, width=250, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame inside canvas
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas reference for cleanup
        self.scrollable_canvas = canvas
        self.mousewheel_handler = _on_mousewheel
        
        # Now use scrollable_frame instead of control_frame for all controls
        control_frame = scrollable_frame
        
        # Title
        title = ttk.Label(control_frame, text="Controls", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Camera controls
        ttk.Label(control_frame, text="Camera:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        self.start_btn = ttk.Button(control_frame, text="Start Webcam", 
                                     command=self.start_camera, width=20)
        self.start_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Webcam", 
                                    command=self.stop_camera, width=20, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Drawing controls
        ttk.Label(control_frame, text="Drawing:", font=("Arial", 10, "bold")).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        ttk.Button(control_frame, text="Clear Canvas", 
                   command=self.clear_canvas, width=20).grid(row=5, column=0, columnspan=2, pady=5)
        
        ttk.Button(control_frame, text="Undo", 
                   command=self.undo_action, width=9).grid(row=6, column=0, pady=5, padx=(0, 5))
        
        ttk.Button(control_frame, text="Redo", 
                   command=self.redo_action, width=9).grid(row=6, column=1, pady=5)
        
        # Color picker
        ttk.Label(control_frame, text="Color:", font=("Arial", 10, "bold")).grid(
            row=7, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.color_var = tk.StringVar(value="red")
        colors = ColorPalette.get_color_names()
        color_menu = ttk.Combobox(control_frame, textvariable=self.color_var, 
                                   values=colors, state="readonly", width=18)
        color_menu.grid(row=8, column=0, columnspan=2, pady=5)
        color_menu.bind("<<ComboboxSelected>>", self.on_color_change)
        
        # Brush size slider
        ttk.Label(control_frame, text="Brush Size:", font=("Arial", 10, "bold")).grid(
            row=9, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.brush_size_var = tk.IntVar(value=5)
        brush_slider = ttk.Scale(control_frame, from_=1, to=20, orient=tk.HORIZONTAL,
                                 variable=self.brush_size_var, command=self.on_brush_size_change)
        brush_slider.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.brush_size_label = ttk.Label(control_frame, text="5 px")
        self.brush_size_label.grid(row=11, column=0, columnspan=2)
        
        # Options
        ttk.Label(control_frame, text="Options:", font=("Arial", 10, "bold")).grid(
            row=12, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.smoothing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Enable Smoothing", 
                        variable=self.smoothing_var,
                        command=self.on_smoothing_toggle).grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.landmarks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Landmarks", 
                        variable=self.landmarks_var,
                        command=self.on_landmarks_toggle).grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Canvas enhancements
        self.grid_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Show Grid", 
                        variable=self.grid_var,
                        command=self.on_grid_toggle).grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.rulers_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Show Rulers", 
                        variable=self.rulers_var,
                        command=self.on_rulers_toggle).grid(row=16, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Brush opacity slider
        ttk.Label(control_frame, text="Brush Opacity:", font=("Arial", 10, "bold")).grid(
            row=17, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.opacity_var = tk.DoubleVar(value=1.0)
        opacity_slider = ttk.Scale(control_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL,
                                   variable=self.opacity_var, command=self.on_opacity_change)
        opacity_slider.grid(row=18, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.opacity_label = ttk.Label(control_frame, text="100%")
        self.opacity_label.grid(row=19, column=0, columnspan=2)
        
        # Shape tools
        ttk.Label(control_frame, text="Shape Tools:", font=("Arial", 10, "bold")).grid(
            row=20, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        shape_frame = ttk.Frame(control_frame)
        shape_frame.grid(row=21, column=0, columnspan=2, pady=5)
        
        ttk.Button(shape_frame, text="○", command=lambda: self.set_shape_mode('circle'), width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(shape_frame, text="□", command=lambda: self.set_shape_mode('rectangle'), width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(shape_frame, text="→", command=lambda: self.set_shape_mode('arrow'), width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(shape_frame, text="─", command=lambda: self.set_shape_mode('line'), width=4).pack(side=tk.LEFT, padx=2)
        
        # Export controls
        ttk.Label(control_frame, text="Export:", font=("Arial", 10, "bold")).grid(
            row=22, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        ttk.Button(control_frame, text="Save Project", 
                   command=self.save_project, width=20).grid(row=23, column=0, columnspan=2, pady=5)
        
        ttk.Button(control_frame, text="Save Image", 
                   command=self.export_image, width=20).grid(row=24, column=0, columnspan=2, pady=5)
        
        self.record_btn = ttk.Button(control_frame, text="Start Recording", 
                                      command=self.toggle_recording, width=20)
        self.record_btn.grid(row=25, column=0, columnspan=2, pady=5)
        
        self.pause_record_btn = ttk.Button(control_frame, text="Pause Recording", 
                                           command=self.pause_recording, width=20, state=tk.DISABLED)
        self.pause_record_btn.grid(row=26, column=0, columnspan=2, pady=5)
        
        ttk.Button(control_frame, text="Load Project", 
                   command=self.load_project, width=20).grid(row=27, column=0, columnspan=2, pady=5)
        
        # Stabilization control
        ttk.Label(control_frame, text="Stabilization:", font=("Arial", 10, "bold")).grid(
            row=28, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.stabilization_var = tk.StringVar(value="high")
        stab_menu = ttk.Combobox(control_frame, textvariable=self.stabilization_var, 
                                 values=['low', 'medium', 'high'], state="readonly", width=18)
        stab_menu.grid(row=29, column=0, columnspan=2, pady=5)
        stab_menu.bind("<<ComboboxSelected>>", self.on_stabilization_change)
        
        # Camera selection
        ttk.Label(control_frame, text="Camera:", font=("Arial", 10, "bold")).grid(
            row=30, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        self.camera_var = tk.IntVar(value=0)
        ttk.Button(control_frame, text="Switch Camera", 
                   command=self.switch_camera, width=20).grid(row=31, column=0, columnspan=2, pady=5)
        
        self.low_light_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Low Light Mode", 
                        variable=self.low_light_var,
                        command=self.on_low_light_toggle).grid(row=32, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Theme control
        ttk.Label(control_frame, text="Theme:", font=("Arial", 10, "bold")).grid(
            row=33, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        theme_frame = ttk.Frame(control_frame)
        theme_frame.grid(row=34, column=0, columnspan=2, pady=5)
        
        ttk.Button(theme_frame, text="Light", command=lambda: self.set_theme('light'), width=9).pack(side=tk.LEFT, padx=2)
        ttk.Button(theme_frame, text="Dark", command=lambda: self.set_theme('dark'), width=9).pack(side=tk.LEFT, padx=2)
    
    def setup_video_panel(self):
        """Setup right video panel"""
        video_frame = ttk.Frame(self.root, padding="10")
        video_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)
        
        # Video canvas
        self.canvas = tk.Canvas(video_frame, width=640, height=480, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder text
        self.canvas.create_text(320, 240, text="Click 'Start Webcam' to begin", 
                                fill="white", font=("Arial", 16), tags="placeholder")
    
    def setup_status_bar(self):
        """Setup bottom status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Gesture label
        ttk.Label(status_frame, text="Gesture:").pack(side=tk.LEFT, padx=5)
        self.gesture_label = ttk.Label(status_frame, text="None", font=("Arial", 10, "bold"))
        self.gesture_label.pack(side=tk.LEFT, padx=5)
        
        # FPS counter
        ttk.Label(status_frame, text="FPS:").pack(side=tk.LEFT, padx=(20, 5))
        self.fps_label = ttk.Label(status_frame, text="0")
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = "Index finger: draw | Index+Middle: navigate | 4 fingers (no thumb): erase | Pinch: change color | Fist: clear"
        self.instruction_label = ttk.Label(status_frame, text=instructions, foreground="blue")
        self.instruction_label.pack(side=tk.LEFT, padx=20)
    
    def show_onboarding(self):
        """Show onboarding popup with gesture tutorial"""
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to AirSig!")
        popup.geometry("600x700")
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Create scrollable frame
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Content
        frame = ttk.Frame(scrollable_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="AirSig - Enhanced Finger Writing", 
                  font=("Arial", 16, "bold")).pack(pady=10)
        
        ttk.Label(frame, text="Hand Gestures:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        gestures = [
            "☝️  Index Finger Only - Draw on canvas",
            "👆 Index + Middle Fingers - Navigate/Move cursor & Shape tools",
            "🖐️  Four Fingers (Thumb Closed) - Erase",
            "✊  Fist (All closed) - Clear entire canvas",
            "🤚  Palm Open (All extended) - Pause drawing",
            "🤏  Pinch (Thumb+Index close) - Cycle through colors"
        ]
        
        for gesture in gestures:
            ttk.Label(frame, text=gesture, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nDrawing Features:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        drawing_features = [
            "🎨 8 Color Palette - Red, Blue, Green, Yellow, Cyan, Magenta, White, Black",
            "🖌️ Adjustable Brush Size (1-20 pixels)",
            "💧 Brush Opacity Control (10-100%)",
            "📐 Shape Tools - Circle, Rectangle, Arrow, Line",
            "↩️  Undo/Redo Support (last 20 actions)",
            "✨ Enhanced Smoothing - Low/Medium/High stabilization levels",
            "🎯 Advanced Stabilization - Jitter reduction for steady lines"
        ]
        
        for feature in drawing_features:
            ttk.Label(frame, text=feature, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nCanvas Tools:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        canvas_tools = [
            "📏 Grid Overlay - 50px spacing for precision",
            "📐 Ruler Markings - On edges for measurements",
            "🔍 Two-Hand Zoom - Pinch gesture with both hands",
            "👁️ Show/Hide Landmarks - Toggle hand tracking visualization"
        ]
        
        for tool in canvas_tools:
            ttk.Label(frame, text=tool, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nProject Management:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        project_features = [
            "💾 Save/Load Projects (.airsig format)",
            "🖼️ Export as Image (PNG/JPEG)",
            "🎬 Video Recording - Record your drawing process",
            "⏸️ Pause/Resume Recording",
            "⏰ Auto-Save - Every 60 seconds (keeps last 5 saves)"
        ]
        
        for feature in project_features:
            ttk.Label(frame, text=feature, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nCamera & Display:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        camera_features = [
            "📷 Multi-Camera Support - Switch between available cameras",
            "🌙 Low Light Mode - Enhanced brightness for dark environments",
            "🎨 UI Themes - Light and Dark mode",
            "📊 Real-time FPS Counter"
        ]
        
        for feature in camera_features:
            ttk.Label(frame, text=feature, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nTips:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        tips = [
            "💡 Keep hand steady for best detection",
            "💡 Use high stabilization for smoother lines",
            "💡 Enable grid and rulers for precise drawings",
            "💡 Projects auto-save to prevent data loss",
            "💡 Use shape tools with navigate gesture (Index+Middle)"
        ]
        
        for tip in tips:
            ttk.Label(frame, text=tip, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        # Close button
        def close_popup():
            canvas.unbind_all("<MouseWheel>")
            popup.destroy()
        
        ttk.Button(frame, text="Got it! Let's Draw!", command=close_popup, width=20).pack(pady=20)
    
    def start_camera(self):
        """Start webcam and video processing"""
        if self.camera_active:
            return
        
        try:
            # Initialize components with improved detection settings
            self.detector = HandDetector(max_hands=2, detection_con=0.8, tracking_con=0.8)
            self.gesture_recognizer = GestureRecognizer()
            self.smoothers = {}
            
            # Open camera with improved settings
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open webcam!\nPlease check if camera is connected and not in use.")
                return
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Enable auto-exposure and auto-focus for better detection
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            
            # Detect available cameras
            self.detect_cameras()
            
            # Read one frame to get actual camera dimensions
            ret, test_frame = self.cap.read()
            if ret:
                actual_height, actual_width = test_frame.shape[:2]
                self.drawing_engine = DrawingEngine(width=actual_width, height=actual_height)
            else:
                self.drawing_engine = DrawingEngine(width=640, height=480)
            
            self.camera_active = True
            self.running = True
            
            # Update buttons
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Remove placeholder
            self.canvas.delete("placeholder")
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.process_video, daemon=True)
            self.video_thread.start()
            
            # Start periodic display update on main thread
            self.update_display_loop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera:\n{str(e)}")
            self.stop_camera()
    
    def update_display_loop(self):
        """Periodic display update on main thread (prevents flickering)"""
        if self.camera_active:
            self.update_display()
            # Schedule next update (30 FPS = ~33ms)
            self.root.after(33, self.update_display_loop)
    
    def stop_camera(self):
        """Stop webcam and video processing"""
        self.running = False
        self.camera_active = False
        
        # Wait for thread to finish
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=2.0)
        
        # Release camera safely
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                print(f"Error releasing camera: {e}")
            finally:
                self.cap = None
        
        # Close detector
        if self.detector:
            try:
                self.detector.close()
            except Exception as e:
                print(f"Error closing detector: {e}")
        
        # Stop recording if active
        if self.recording:
            self.toggle_recording()
        
        # Unbind mousewheel
        if hasattr(self, 'scrollable_canvas') and hasattr(self, 'mousewheel_handler'):
            try:
                self.scrollable_canvas.unbind_all("<MouseWheel>")
            except Exception as e:
                print(f"Error unbinding mousewheel: {e}")
        
        # Update buttons
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # Show placeholder
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text="Camera stopped", 
                                fill="white", font=("Arial", 16), tags="placeholder")
    
    def process_video(self):
        """Main video processing loop (runs in separate thread)"""
        prev_time = time.time()
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Apply low-light enhancement if enabled
                if self.low_light_mode:
                    # Increase brightness and contrast for low light
                    frame = cv2.convertScaleAbs(frame, alpha=self.contrast_adjustment, beta=self.brightness_adjustment)
                
                # Enhance frame for better hand detection
                # Slight Gaussian blur to reduce noise
                frame = cv2.GaussianBlur(frame, (3, 3), 0)
                
                # Enhance brightness and contrast slightly (if not in low-light mode)
                if not self.low_light_mode:
                    frame = cv2.convertScaleAbs(frame, alpha=self.contrast_adjustment, beta=self.brightness_adjustment)
                
                # Detect hands
                frame = self.detector.find_hands(frame, draw=self.show_landmarks, 
                                                 draw_landmarks=self.show_landmarks)
                
                # Get all hands
                hands_data = self.detector.get_all_hands(frame)
                
                # Process gestures
                self.process_gestures(hands_data, frame)
                
                # Overlay drawing on frame
                frame = self.drawing_engine.overlay_on_frame(frame)
                
                # Draw grid if enabled
                if self.show_grid:
                    self.draw_grid(frame)
                
                # Draw rulers if enabled
                if self.show_rulers:
                    self.draw_rulers(frame)
                
                # Calculate FPS
                self.fps, prev_time = calculate_fps(prev_time)
                
                # Draw FPS on frame
                cv2.putText(frame, f"FPS: {int(self.fps)}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Record frame if recording and not paused (with memory limit)
                if self.recording and not self.recording_paused:
                    # Limit buffer to prevent memory issues (max 10 minutes at 30fps = 18000 frames)
                    if len(self.recorded_frames) < 18000:
                        self.recorded_frames.append(frame.copy())
                    else:
                        # Buffer full, stop recording automatically
                        self.root.after(0, lambda: messagebox.showwarning(
                            "Recording", "Recording buffer full (10 minutes). Stopping recording."
                        ))
                        self.root.after(10, self.toggle_recording)
                
                # Check auto-save
                self.auto_save_check()
                
                # Update GUI
                with self.thread_lock:
                    self.current_frame = frame.copy()
                
                # Small delay to prevent high CPU usage
                time.sleep(0.01)  # 10ms delay for ~100 FPS max
                
            except Exception as e:
                print(f"Video processing error: {e}")
                time.sleep(0.1)  # Wait before retrying
    
    def process_gestures(self, hands_data, frame):
        """Process hand gestures and update drawing"""
        if not hands_data:
            self.current_gesture = "none"
            self.prev_draw_point = None
            return
        
        # Process each hand
        for idx, hand in enumerate(hands_data):
            landmarks = hand['landmarks']
            hand_type = hand['hand_type']
            
            if not landmarks:
                continue
            
            # Get gesture
            gesture, confidence = self.gesture_recognizer.recognize(landmarks, hand_type)
            
            # Get finger tip position (index finger - landmark 8)
            if len(landmarks) > 8:
                finger_tip = (landmarks[8][1], landmarks[8][2])
                
                # Apply smoothing if enabled
                if self.smoothing_enabled:
                    if idx not in self.smoothers:
                        self.smoothers[idx] = PointSmoother(
                            jitter_threshold=self.jitter_threshold,
                            stabilization=self.stabilization_level
                        )
                    finger_tip = self.smoothers[idx].smooth(finger_tip)
                else:
                    if idx in self.smoothers:
                        self.smoothers[idx].reset()
                
                # Handle gestures
                if gesture == "draw":
                    # Draw mode
                    if self.prev_draw_point:
                        # Apply opacity to brush color
                        color_with_opacity = self.brush_color
                        if self.brush_opacity < 1.0:
                            # For opacity, we'll blend with white background
                            color_with_opacity = tuple(int(c * self.brush_opacity + 255 * (1 - self.brush_opacity)) 
                                                      for c in self.brush_color)
                        
                        self.drawing_engine.draw_line(self.prev_draw_point, finger_tip, 
                                                      color_with_opacity, self.brush_size)
                        self.project_modified = True  # Mark as modified
                    else:
                        # Starting new stroke, save undo state
                        self.drawing_engine.save_state()
                    self.prev_draw_point = finger_tip
                    self.current_gesture = "Drawing"
                
                elif gesture == "navigate":
                    # Navigation mode - show cursor
                    cv2.circle(frame, finger_tip, 10, (255, 255, 0), 2)
                    self.prev_draw_point = None
                    
                    # Shape tool interaction
                    if self.shape_mode and idx == 0:  # Only first hand
                        self.handle_shape_tool(finger_tip)
                    
                    self.current_gesture = "Navigate"
                
                elif gesture == "erase":
                    # Erase mode
                    if self.prev_draw_point is None:
                        # Starting new erase stroke, save undo state
                        self.drawing_engine.save_state()
                    self.drawing_engine.erase(finger_tip, self.eraser_size)
                    cv2.circle(frame, finger_tip, self.eraser_size, (0, 0, 0), 2)
                    self.prev_draw_point = finger_tip  # Track for state saving
                    self.current_gesture = "Erasing"
                    self.project_modified = True
                
                elif gesture == "fist":
                    # Clear canvas
                    self.drawing_engine.clear()
                    self.prev_draw_point = None
                    self.current_gesture = "Clear All"
                    self.project_modified = True
                
                elif gesture == "palm_open":
                    # Pause
                    self.prev_draw_point = None
                    self.current_gesture = "Paused"
                
                elif gesture == "pinch":
                    # Cycle through colors on pinch
                    # Only change color on new pinch (not continuous)
                    if not self.last_pinch_state:
                        self.current_color_index = (self.current_color_index + 1) % len(self.color_list)
                        color_name = self.color_list[self.current_color_index]
                        self.brush_color = ColorPalette.get_color(color_name)
                        
                        # Update color dropdown
                        self.color_var.set(color_name)
                        
                        self.last_pinch_state = True
                        self.current_gesture = f"Color Changed: {color_name.title()}"
                    else:
                        self.current_gesture = "Pinch (Hold)"
                    
                    self.prev_draw_point = None
                
                else:
                    self.prev_draw_point = None
                    self.current_gesture = "Unknown"
                    self.last_pinch_state = False
            
            # Reset pinch state if not pinching
            if gesture != "pinch":
                self.last_pinch_state = False
    
    def update_display(self):
        """Update video display on canvas"""
        if self.current_frame is None or not self.camera_active:
            return
        
        try:
            with self.thread_lock:
                frame = self.current_frame.copy()
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            img = Image.fromarray(frame_rgb)
            
            # Resize to fit canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Only resize if canvas has valid dimensions
            if canvas_width > 1 and canvas_height > 1:
                img = img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo  # Keep a reference
            
            # Update status labels (less frequently to reduce overhead)
            if hasattr(self, '_last_status_update'):
                if time.time() - self._last_status_update > 0.1:  # Update every 100ms
                    self.gesture_label.config(text=self.current_gesture)
                    self.fps_label.config(text=str(int(self.fps)))
                    self._last_status_update = time.time()
            else:
                self._last_status_update = time.time()
                self.gesture_label.config(text=self.current_gesture)
                self.fps_label.config(text=str(int(self.fps)))
            
        except tk.TclError:
            # Window closed or widget destroyed
            pass
        except Exception as e:
            print(f"Display update error: {e}")
    
    def clear_canvas(self):
        """Clear the drawing canvas"""
        if self.drawing_engine:
            self.drawing_engine.clear()
    
    def undo_action(self):
        """Undo last drawing action"""
        if self.drawing_engine:
            self.drawing_engine.undo()
    
    def redo_action(self):
        """Redo last undone action"""
        if self.drawing_engine:
            self.drawing_engine.redo()
    
    def on_color_change(self, event):
        """Handle color selection change"""
        color_name = self.color_var.get()
        self.brush_color = ColorPalette.get_color(color_name)
    
    def on_brush_size_change(self, value):
        """Handle brush size slider change"""
        self.brush_size = int(float(value))
        self.brush_size_label.config(text=f"{self.brush_size} px")
        self.eraser_size = self.brush_size * 3  # Eraser is 3x brush size
    
    def on_smoothing_toggle(self):
        """Handle smoothing checkbox toggle"""
        self.smoothing_enabled = self.smoothing_var.get()
        # Reset smoothers
        self.smoothers = {}
    
    def on_landmarks_toggle(self):
        """Handle landmarks checkbox toggle"""
        self.show_landmarks = self.landmarks_var.get()
    
    def on_grid_toggle(self):
        """Handle grid checkbox toggle"""
        self.show_grid = self.grid_var.get()
    
    def on_rulers_toggle(self):
        """Handle rulers checkbox toggle"""
        self.show_rulers = self.rulers_var.get()
    
    def on_stabilization_change(self, event):
        """Handle stabilization level change"""
        self.stabilization_level = self.stabilization_var.get()
        # Update filter parameters based on level
        if self.stabilization_level == 'low':
            self.jitter_threshold = 3
        elif self.stabilization_level == 'medium':
            self.jitter_threshold = 5
        else:  # high
            self.jitter_threshold = 8
        # Reset smoothers to apply new settings
        self.smoothers = {}
    
    def switch_camera(self):
        """Switch to next available camera"""
        if not self.camera_active:
            messagebox.showinfo("Camera", "Start camera first!")
            return
        
        # Detect available cameras
        if not self.available_cameras:
            self.detect_cameras()
        
        if len(self.available_cameras) > 1:
            # Switch to next camera
            self.camera_index = (self.camera_index + 1) % len(self.available_cameras)
            # Restart camera with new index
            self.stop_camera()
            time.sleep(0.5)
            self.start_camera()
            messagebox.showinfo("Camera", f"Switched to camera {self.camera_index}")
        else:
            messagebox.showinfo("Camera", "Only one camera detected")
    
    def detect_cameras(self):
        """Detect available cameras"""
        self.available_cameras = []
        for i in range(5):  # Check first 5 indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.available_cameras.append(i)
                cap.release()
    
    def on_low_light_toggle(self):
        """Handle low light mode toggle"""
        self.low_light_mode = self.low_light_var.get()
        if self.low_light_mode:
            self.brightness_adjustment = 20
            self.contrast_adjustment = 1.2
        else:
            self.brightness_adjustment = 10
            self.contrast_adjustment = 1.1
    
    def set_theme(self, theme):
        """Set UI theme"""
        self.current_theme = theme
        
        if theme == 'dark':
            # Dark theme colors
            bg_color = '#2b2b2b'
            fg_color = '#ffffff'
            self.root.configure(bg=bg_color)
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('.', background=bg_color, foreground=fg_color)
            style.configure('TLabel', background=bg_color, foreground=fg_color)
            style.configure('TFrame', background=bg_color)
            style.configure('TButton', background='#404040', foreground=fg_color)
            messagebox.showinfo("Theme", "Dark theme applied")
        else:
            # Light theme (default)
            style = ttk.Style()
            style.theme_use('vista')
            messagebox.showinfo("Theme", "Light theme applied")
    
    def export_image(self):
        """Export drawing as image"""
        if not self.drawing_engine:
            messagebox.showwarning("Warning", "Start camera first!")
            return
        
        # Get save path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"airsig_drawing_{timestamp}.png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if filename:
            canvas = self.drawing_engine.get_canvas()
            cv2.imwrite(filename, canvas)
            messagebox.showinfo("Export", f"Image saved to:\n{filename}")
            self.project_modified = False
    
    def on_opacity_change(self, value):
        """Handle opacity slider change"""
        self.brush_opacity = float(value)
        self.opacity_label.config(text=f"{int(self.brush_opacity * 100)}%")
    
    def set_shape_mode(self, shape):
        """Set the current shape drawing mode"""
        if self.shape_mode == shape:
            self.shape_mode = None  # Toggle off
            messagebox.showinfo("Shape Tool", "Shape mode disabled")
        else:
            self.shape_mode = shape
            messagebox.showinfo("Shape Tool", f"Drawing {shape}. Use Index+Middle fingers to set points.")
    
    def save_project(self):
        """Save current project with all settings"""
        if not self.drawing_engine:
            messagebox.showwarning("Warning", "No drawing to save!")
            return
        
        # Get save path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".airsig",
            initialfile=f"airsig_project_{timestamp}.airsig",
            filetypes=[("AirSig Project", "*.airsig"), ("All files", "*.*")]
        )
        
        if filename:
            import pickle
            project_data = {
                'canvas': self.drawing_engine.get_canvas(),
                'brush_color': self.brush_color,
                'brush_size': self.brush_size,
                'brush_opacity': self.brush_opacity,
                'eraser_size': self.eraser_size,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'wb') as f:
                pickle.dump(project_data, f)
            
            self.current_project_path = filename
            self.project_modified = False
            messagebox.showinfo("Save Project", f"Project saved to:\n{filename}")
    
    def load_project(self):
        """Load a saved project"""
        filename = filedialog.askopenfilename(
            filetypes=[("AirSig Project", "*.airsig"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import pickle
                with open(filename, 'rb') as f:
                    project_data = pickle.load(f)
                
                # Validate project data
                if not isinstance(project_data, dict):
                    raise ValueError("Invalid project file format")
                
                if 'canvas' not in project_data:
                    raise ValueError("Project file missing canvas data")
                
                # Restore drawing
                if self.drawing_engine:
                    # Validate canvas dimensions
                    canvas_data = project_data['canvas']
                    if not isinstance(canvas_data, np.ndarray) or len(canvas_data.shape) != 3:
                        raise ValueError("Invalid canvas data format")
                    
                    self.drawing_engine.canvas = canvas_data
                    self.brush_color = project_data.get('brush_color', (0, 0, 255))
                    self.brush_size = project_data.get('brush_size', 5)
                    self.brush_opacity = project_data.get('brush_opacity', 1.0)
                    self.eraser_size = project_data.get('eraser_size', 20)
                    
                    # Update UI
                    self.brush_size_var.set(self.brush_size)
                    self.opacity_var.set(self.brush_opacity)
                    
                    self.current_project_path = filename
                    self.project_modified = False
                    messagebox.showinfo("Load Project", "Project loaded successfully!")
                else:
                    messagebox.showwarning("Warning", "Start camera first!")
            except (pickle.UnpicklingError, ValueError, KeyError) as e:
                messagebox.showerror("Error", f"Invalid or corrupted project file:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project:\n{str(e)}")
    
    def auto_save_check(self):
        """Check if auto-save is needed"""
        if self.auto_save_enabled and self.project_modified and self.drawing_engine:
            current_time = time.time()
            if current_time - self.last_auto_save >= self.auto_save_interval:
                try:
                    self.auto_save()
                    self.last_auto_save = current_time
                except Exception as e:
                    print(f"Auto-save error: {e}")
    
    def auto_save(self):
        """Perform auto-save"""
        if not self.drawing_engine:
            return
        
        # Create autosave directory if it doesn't exist
        autosave_dir = os.path.join(os.path.dirname(__file__), 'autosave')
        os.makedirs(autosave_dir, exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(autosave_dir, f"autosave_{timestamp}.airsig")
        
        import pickle
        project_data = {
            'canvas': self.drawing_engine.get_canvas(),
            'brush_color': self.brush_color,
            'brush_size': self.brush_size,
            'brush_opacity': self.brush_opacity,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(project_data, f)
        
        # Keep only last 5 autosaves
        autosaves = sorted([f for f in os.listdir(autosave_dir) if f.startswith('autosave_')])
        if len(autosaves) > 5:
            for old_file in autosaves[:-5]:
                os.remove(os.path.join(autosave_dir, old_file))
    
    def pause_recording(self):
        """Pause or resume recording"""
        if self.recording:
            self.recording_paused = not self.recording_paused
            if self.recording_paused:
                self.pause_record_btn.config(text="Resume Recording")
                messagebox.showinfo("Recording", "Recording paused")
            else:
                self.pause_record_btn.config(text="Pause Recording")
                messagebox.showinfo("Recording", "Recording resumed")
    
    def toggle_recording(self):
        """Toggle video recording"""
        if not self.recording:
            # Start recording
            self.recording = True
            self.recording_paused = False
            self.recording_start_time = time.time()
            self.recorded_frames = []
            self.recording_timestamps = []
            self.record_btn.config(text="Stop Recording")
            self.pause_record_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Recording", "Video recording started")
        else:
            # Stop recording and save
            self.recording = False
            self.recording_paused = False
            self.record_btn.config(text="Start Recording")
            self.pause_record_btn.config(state=tk.DISABLED, text="Pause Recording")
            
            if self.recorded_frames:
                # Get save path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = filedialog.asksaveasfilename(
                    defaultextension=".avi",
                    initialfile=f"airsig_recording_{timestamp}.avi",
                    filetypes=[("AVI files", "*.avi"), ("MP4 files", "*.mp4"), ("All files", "*.*")]
                )
                
                if filename:
                    # Save video
                    height, width = self.recorded_frames[0].shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
                    
                    for frame in self.recorded_frames:
                        out.write(frame)
                    
                    out.release()
                    self.recorded_frames = []
                    messagebox.showinfo("Recording", f"Video saved to:\n{filename}")
            else:
                messagebox.showwarning("Recording", "No frames recorded!")
    
    def handle_shape_tool(self, point):
        """Handle shape tool drawing with navigation gesture"""
        if not self.shape_start_point:
            # First point
            self.shape_start_point = point
            messagebox.showinfo("Shape Tool", "First point set. Move to second point and use navigate gesture.")
        else:
            # Second point - draw the shape
            if self.shape_mode == 'circle':
                center = ((self.shape_start_point[0] + point[0]) // 2,
                         (self.shape_start_point[1] + point[1]) // 2)
                radius = int(np.sqrt((point[0] - self.shape_start_point[0])**2 + 
                                    (point[1] - self.shape_start_point[1])**2) // 2)
                cv2.circle(self.drawing_engine.canvas, center, radius, self.brush_color, self.brush_size)
            
            elif self.shape_mode == 'rectangle':
                cv2.rectangle(self.drawing_engine.canvas, self.shape_start_point, point, 
                            self.brush_color, self.brush_size)
            
            elif self.shape_mode == 'line':
                cv2.line(self.drawing_engine.canvas, self.shape_start_point, point, 
                        self.brush_color, self.brush_size, cv2.LINE_AA)
            
            elif self.shape_mode == 'arrow':
                cv2.arrowedLine(self.drawing_engine.canvas, self.shape_start_point, point, 
                              self.brush_color, self.brush_size, tipLength=0.3)
            
            # Reset shape tool
            self.shape_start_point = None
            self.shape_mode = None
            self.project_modified = True
            messagebox.showinfo("Shape Tool", "Shape completed!")
    
    def process_two_hand_gestures(self, hands_data, frame):
        """Two-hand gestures disabled"""
        pass
    
    def draw_grid(self, frame):
        """Draw grid overlay on frame"""
        h, w = frame.shape[:2]
        grid_color = (100, 100, 100)
        
        # Vertical lines
        for x in range(0, w, self.grid_size):
            cv2.line(frame, (x, 0), (x, h), grid_color, 1)
        
        # Horizontal lines
        for y in range(0, h, self.grid_size):
            cv2.line(frame, (0, y), (w, y), grid_color, 1)
    
    def draw_rulers(self, frame):
        """Draw ruler markings on frame edges"""
        h, w = frame.shape[:2]
        ruler_color = (200, 200, 200)
        text_color = (255, 255, 255)
        
        # Top ruler
        for x in range(0, w, 50):
            cv2.line(frame, (x, 0), (x, 10), ruler_color, 1)
            if x % 100 == 0:
                cv2.putText(frame, str(x), (x + 2, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
        
        # Left ruler
        for y in range(0, h, 50):
            cv2.line(frame, (0, y), (10, y), ruler_color, 1)
            if y % 100 == 0:
                cv2.putText(frame, str(y), (12, y + 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
    
    def on_closing(self):
        """Handle window close event"""
        if self.camera_active:
            self.stop_camera()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AirSigGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
