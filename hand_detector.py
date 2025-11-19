"""
Enhanced HandDetector class using MediaPipe Hands
Supports dual hand detection and improved landmark extraction
"""

import cv2
import mediapipe as mp
import numpy as np


class HandDetector:
    """
    MediaPipe Hands wrapper for robust hand detection and tracking
    Supports multiple hands and provides landmarks with handedness
    """
    
    def __init__(self, mode=False, max_hands=2, model_complexity=1, 
                 detection_con=0.7, tracking_con=0.7):
        """
        Initialize HandDetector
        
        Args:
            mode: Static image mode (False for video)
            max_hands: Maximum number of hands to detect (1-2)
            model_complexity: Model complexity (0 or 1)
            detection_con: Minimum detection confidence (increased to 0.7 for better accuracy)
            tracking_con: Minimum tracking confidence (increased to 0.7 for smoother tracking)
        """
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_con = detection_con
        self.tracking_con = tracking_con
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.tracking_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Store results
        self.results = None
        self.hands_data = []
    
    def find_hands(self, frame, draw=True, draw_landmarks=True):
        """
        Detect hands in frame
        
        Args:
            frame: Input frame (BGR)
            draw: Whether to draw landmarks
            draw_landmarks: Whether to draw detailed landmarks
        
        Returns:
            frame: Frame with drawings (if draw=True)
        """
        # Convert to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        self.results = self.hands.process(frame_rgb)
        
        # Draw landmarks
        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                else:
                    # Simple circle drawing
                    h, w, c = frame.shape
                    for lm in hand_landmarks.landmark:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
        
        return frame
    
    def find_positions(self, frame, hand_no=0, draw=False):
        """
        Get landmark positions for a specific hand
        
        Args:
            frame: Input frame
            hand_no: Hand index (0 for first, 1 for second)
            draw: Whether to draw landmarks
        
        Returns:
            lm_list: List of [id, x, y] for each landmark
        """
        lm_list = []
        
        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_no]
                h, w, c = frame.shape
                
                for id, lm in enumerate(hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                    
                    if draw:
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        
        return lm_list
    
    def get_all_hands(self, frame):
        """
        Get data for all detected hands
        
        Returns:
            hands_data: List of dicts with 'landmarks', 'handedness', 'hand_type'
        """
        self.hands_data = []
        
        if self.results and self.results.multi_hand_landmarks:
            h, w, c = frame.shape
            
            for idx, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
                # Get landmarks
                lm_list = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                
                # Get handedness (Left/Right)
                hand_type = "Unknown"
                if self.results.multi_handedness and idx < len(self.results.multi_handedness):
                    hand_type = self.results.multi_handedness[idx].classification[0].label
                
                self.hands_data.append({
                    'landmarks': lm_list,
                    'handedness': hand_type,
                    'hand_type': hand_type
                })
        
        return self.hands_data
    
    def get_finger_states(self, lm_list, hand_type="Right"):
        """
        Determine which fingers are extended
        
        Args:
            lm_list: Landmark list
            hand_type: "Left" or "Right"
        
        Returns:
            fingers: List of [thumb, index, middle, ring, pinky] (1=up, 0=down)
        """
        if not lm_list or len(lm_list) < 21:
            return [0, 0, 0, 0, 0]
        
        fingers = []
        
        # Thumb - check x coordinate (different for left/right hand)
        if hand_type == "Right":
            if lm_list[4][1] < lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:  # Left hand
            if lm_list[4][1] > lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        # Other fingers - check y coordinate
        finger_tips = [8, 12, 16, 20]
        for tip_id in finger_tips:
            if lm_list[tip_id][2] < lm_list[tip_id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def find_distance(self, p1, p2, frame=None, draw=True):
        """
        Calculate distance between two landmarks
        
        Args:
            p1: First point [id, x, y]
            p2: Second point [id, x, y]
            frame: Frame to draw on
            draw: Whether to draw line
        
        Returns:
            length: Distance between points
            info: [x1, y1, x2, y2, cx, cy]
        """
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        if frame is not None and draw:
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(frame, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
        
        return length, [x1, y1, x2, y2, cx, cy]
    
    def close(self):
        """Release resources"""
        if self.hands:
            self.hands.close()


def main():
    """Test HandDetector"""
    cap = cv2.VideoCapture(0)
    detector = HandDetector(max_hands=2)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        frame = detector.find_hands(frame)
        
        # Get all hands
        hands_data = detector.get_all_hands(frame)
        
        for hand in hands_data:
            lm_list = hand['landmarks']
            hand_type = hand['hand_type']
            
            if lm_list:
                fingers = detector.get_finger_states(lm_list, hand_type)
                print(f"{hand_type} hand: {fingers}")
        
        cv2.imshow('Hand Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    detector.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
