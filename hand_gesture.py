import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

def count_fingers(hand_landmarks):
    """Enhanced finger counting algorithm with improved accuracy"""
    if not hand_landmarks:
        return 0
        
    points = hand_landmarks.landmark
    fingers = 0
    
    # Thumb - improved angle-based detection
    thumb_tip = points[4]
    thumb_ip = points[3]
    thumb_mcp = points[2]
    
    # Calculate angle between thumb segments
    angle = np.degrees(np.arctan2(
        thumb_tip.y - thumb_ip.y,
        thumb_tip.x - thumb_ip.x
    ) - np.arctan2(
        thumb_mcp.y - thumb_ip.y,
        thumb_mcp.x - thumb_ip.x
    ))
    
    # Normalize angle to 0-180
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
        
    # Thumb is considered raised if angle is greater than threshold
    if angle > 30:
        fingers += 1
        
    # Other fingers - improved with distance and angle checks
    tips = [8, 12, 16, 20]  # Fingertip indices
    pips = [6, 10, 14, 18]  # PIP joint indices (middle knuckle)
    mcps = [5, 9, 13, 17]   # MCP joint indices (base knuckle)
    
    for tip, pip, mcp in zip(tips, pips, mcps):
        # Calculate finger extension using both height and angle
        height_check = points[tip].y < points[pip].y
        
        # Calculate angle between finger segments
        angle = np.degrees(np.arctan2(
            points[tip].y - points[pip].y,
            points[tip].x - points[pip].x
        ) - np.arctan2(
            points[mcp].y - points[pip].y,
            points[mcp].x - points[pip].x
        ))
        
        # Normalize angle
        angle = abs(angle)
        if angle > 180:
            angle = 360 - angle
            
        # Finger is considered raised if it's extended and at a sufficient angle
        if height_check and angle > 20:
            fingers += 1
            
    return fingers

class GestureController:
    def __init__(self):
        self.drawing = mp.solutions.drawing_utils
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh()
        self.cap = None
        self.prev_gesture = None
        self.gesture_start_time = 0
        self.gesture_cooldown = 0.3  # Seconds between gesture recognition
    
    def initialize_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            return self.cap.isOpened()
        return True
    
    def process_frame(self):
        if not self.initialize_camera():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Flip frame for more intuitive interaction
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hands
        hand_results = self.hands.process(rgb_frame)
        face_results = self.face_mesh.process(rgb_frame)
        
        current_time = time.time()
        gesture = None
        
        if hand_results.multi_hand_landmarks:
            hand_landmarks = hand_results.multi_hand_landmarks[0]
            self.drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            
            # Process gesture with cooldown
            if current_time - self.gesture_start_time >= self.gesture_cooldown:
                finger_count = count_fingers(hand_landmarks)
                
                if finger_count != self.prev_gesture:
                    gesture = self.get_gesture_from_count(finger_count)
                    if gesture:
                        self.execute_gesture(gesture)
                        self.prev_gesture = finger_count
                        self.gesture_start_time = current_time
        
        # Process face for auto-pause
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                self.drawing.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp.solutions.face_mesh.FACEMESH_CONTOURS
                )
        
        return frame
    
    def get_gesture_from_count(self, count):
        gesture_map = {
            1: 'right',
            2: 'left',
            3: 'up',
            4: 'down',
            5: 'space'
        }
        return gesture_map.get(count)
    
    def execute_gesture(self, gesture):
        pyautogui.press(gesture)
    
    def cleanup(self):
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

def main():
    controller = GestureController()
    
    try:
        while True:
            frame = controller.process_frame()
            if frame is None:
                print("Error capturing frame")
                break
            
            cv2.namedWindow("Gesture Control Camera", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Gesture Control Camera", 320, 240)
            cv2.moveWindow("Gesture Control Camera", 1024, 480)  # Position window at bottom right
            cv2.imshow("Gesture Control Camera", frame)
            if cv2.waitKey(1) == 27:  # ESC key
                break
    
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()