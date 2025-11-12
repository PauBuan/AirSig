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
        self.eraser_size = 20
        self.smoothing_enabled = True
        self.show_landmarks = True
        
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
        self.video_writer = None
        self.recorded_frames = []
        
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
        """Setup left control panel"""
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W), padx=5, pady=5)
        
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
                        command=self.on_smoothing_toggle).grid(row=13, column=0, columnspan=2, sticky=tk.W)
        
        self.landmarks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Landmarks", 
                        variable=self.landmarks_var,
                        command=self.on_landmarks_toggle).grid(row=14, column=0, columnspan=2, sticky=tk.W)
        
        # Export controls
        ttk.Label(control_frame, text="Export:", font=("Arial", 10, "bold")).grid(
            row=15, column=0, columnspan=2, sticky=tk.W, pady=(20, 5)
        )
        
        ttk.Button(control_frame, text="Save Image", 
                   command=self.export_image, width=20).grid(row=16, column=0, columnspan=2, pady=5)
        
        self.record_btn = ttk.Button(control_frame, text="Start Recording", 
                                      command=self.toggle_recording, width=20)
        self.record_btn.grid(row=17, column=0, columnspan=2, pady=5)
    
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
        instructions = "Point index finger to draw | Index+Middle to navigate | All fingers to erase | Fist to clear | Palm open to pause"
        self.instruction_label = ttk.Label(status_frame, text=instructions, foreground="blue")
        self.instruction_label.pack(side=tk.LEFT, padx=20)
    
    def show_onboarding(self):
        """Show onboarding popup with gesture tutorial"""
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to AirSig!")
        popup.geometry("500x400")
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Content
        frame = ttk.Frame(popup, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="AirSig - Finger Writing Tutorial", 
                  font=("Arial", 16, "bold")).pack(pady=10)
        
        ttk.Label(frame, text="Gestures:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        gestures = [
            "✏️  Index Finger Only - Draw on canvas",
            "👆 Index + Middle Fingers - Navigate/Move cursor",
            "🖐️  All Fingers Extended - Erase",
            "✊  Fist (All closed) - Clear entire canvas",
            "🤚  Palm Open - Pause drawing",
            "🤏  Pinch (Thumb+Index close) - Change color/size"
        ]
        
        for gesture in gestures:
            ttk.Label(frame, text=gesture, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Label(frame, text="\nControls:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        controls = [
            "• Use left panel to adjust brush size and color",
            "• Enable smoothing for smoother lines",
            "• Export your drawing as an image",
            "• Record video of your drawing session"
        ]
        
        for control in controls:
            ttk.Label(frame, text=control, font=("Arial", 10)).pack(anchor=tk.W, pady=2, padx=10)
        
        ttk.Button(frame, text="Got it!", command=popup.destroy, width=15).pack(pady=20)
    
    def start_camera(self):
        """Start webcam and video processing"""
        if self.camera_active:
            return
        
        # Initialize components
        self.detector = HandDetector(max_hands=2, detection_con=0.7, tracking_con=0.5)
        self.drawing_engine = DrawingEngine(width=640, height=480)
        self.gesture_recognizer = GestureRecognizer()
        self.smoothers = {}
        
        # Open camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam!")
            return
        
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
            self.video_thread.join(timeout=1.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Close detector
        if self.detector:
            self.detector.close()
        
        # Stop recording if active
        if self.recording:
            self.toggle_recording()
        
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
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect hands
            frame = self.detector.find_hands(frame, draw=self.show_landmarks, 
                                             draw_landmarks=self.show_landmarks)
            
            # Get all hands
            hands_data = self.detector.get_all_hands(frame)
            
            # Process gestures
            self.process_gestures(hands_data, frame)
            
            # Overlay drawing on frame
            frame = self.drawing_engine.overlay_on_frame(frame)
            
            # Calculate FPS
            self.fps, prev_time = calculate_fps(prev_time)
            
            # Draw FPS on frame
            cv2.putText(frame, f"FPS: {int(self.fps)}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Record frame if recording
            if self.recording:
                self.recorded_frames.append(frame.copy())
            
            # Update GUI
            with self.thread_lock:
                self.current_frame = frame.copy()
            
            # Small delay to prevent high CPU usage
            time.sleep(0.01)  # 10ms delay for ~100 FPS max
    
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
                        self.smoothers[idx] = PointSmoother()
                    finger_tip = self.smoothers[idx].smooth(finger_tip)
                else:
                    if idx in self.smoothers:
                        self.smoothers[idx].reset()
                
                # Handle gestures
                if gesture == "draw":
                    # Draw mode
                    if self.prev_draw_point:
                        self.drawing_engine.draw_line(self.prev_draw_point, finger_tip, 
                                                      self.brush_color, self.brush_size)
                    self.prev_draw_point = finger_tip
                    self.current_gesture = "Drawing"
                
                elif gesture == "navigate":
                    # Navigation mode - show cursor
                    cv2.circle(frame, finger_tip, 10, (255, 255, 0), 2)
                    self.prev_draw_point = None
                    self.current_gesture = "Navigate"
                
                elif gesture == "erase":
                    # Erase mode
                    self.drawing_engine.erase(finger_tip, self.eraser_size)
                    cv2.circle(frame, finger_tip, self.eraser_size, (0, 0, 0), 2)
                    self.prev_draw_point = None
                    self.current_gesture = "Erasing"
                
                elif gesture == "fist":
                    # Clear canvas
                    self.drawing_engine.clear()
                    self.prev_draw_point = None
                    self.current_gesture = "Clear All"
                
                elif gesture == "palm_open":
                    # Pause
                    self.prev_draw_point = None
                    self.current_gesture = "Paused"
                
                elif gesture == "pinch":
                    # Color/size change indicator
                    self.prev_draw_point = None
                    self.current_gesture = "Pinch (Change Settings)"
                
                else:
                    self.prev_draw_point = None
                    self.current_gesture = "Unknown"
    
    def update_display(self):
        """Update video display on canvas"""
        if self.current_frame is None:
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
            
            if canvas_width > 1 and canvas_height > 1:
                img = img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo  # Keep a reference
            
            # Update status labels
            self.gesture_label.config(text=self.current_gesture)
            self.fps_label.config(text=str(int(self.fps)))
            
        except Exception as e:
            print(f"Display update error: {e}")
    
    def clear_canvas(self):
        """Clear the drawing canvas"""
        if self.drawing_engine:
            self.drawing_engine.clear()
    
    def undo_action(self):
        """Undo last drawing action"""
        if self.drawing_engine:
            if self.drawing_engine.undo():
                messagebox.showinfo("Undo", "Last action undone")
            else:
                messagebox.showinfo("Undo", "Nothing to undo")
    
    def redo_action(self):
        """Redo last undone action"""
        if self.drawing_engine:
            if self.drawing_engine.redo():
                messagebox.showinfo("Redo", "Action redone")
            else:
                messagebox.showinfo("Redo", "Nothing to redo")
    
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
    
    def toggle_recording(self):
        """Toggle video recording"""
        if not self.recording:
            # Start recording
            self.recording = True
            self.recorded_frames = []
            self.record_btn.config(text="Stop Recording")
            messagebox.showinfo("Recording", "Video recording started")
        else:
            # Stop recording and save
            self.recording = False
            self.record_btn.config(text="Start Recording")
            
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
