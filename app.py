from flask import Flask, render_template, Response, request, jsonify, send_from_directory, redirect, url_for, session
import cv2
import numpy as np
import mediapipe as mp
import os
import requests
from werkzeug.utils import secure_filename
import pyautogui
import logging
import math
import time
import json
from functools import wraps
from database import create_token, verify_token
from flask_cors import CORS
import base64
from youtube_api import get_youtube_data, search_videos, get_video_details
from movie_models import MovieFavorite, MovieHistory
import http.client
from flask_sock import Sock
from config import YOUTUBE_API_KEY, YOUTUBE_API_BASE_URL, YOUTUBE_RESULTS_PER_PAGE, DEFAULT_SEARCH_QUERY
import isodate

app = Flask(__name__)
CORS(app)
sock = Sock(app)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.logger.setLevel(logging.DEBUG)
app.config['SITE_NAME'] = 'QuantumGaze'

# Global variables
gesture_control_enabled = False
current_video = None
face_present = True
last_pause_time = 0
eyes_closed = False
video_gesture_control_enabled = True
last_gesture_time = time.time()
MIN_GESTURE_INTERVAL = 0.5  # Minimum time between gestures

# Initialize MediaPipe components
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize detectors with improved settings
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# Initialize face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

@app.route('/')
def index():
    return render_template('index.html', current_user=None)

@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    if not video_id:
        return redirect(url_for('movies'))
        
    # Add to watch history
    video_details = get_video_details(video_id)
    if video_details.get('success'):
        MovieHistory.add_to_history('default_user', video_id, video_details['video'])
        
    return render_template('watch.html', video_id=video_id, current_user=None)

@app.route('/movies')
def movies():
    return render_template('movies.html', current_user=None)

@app.route('/features')
def features():
    return render_template('features.html', current_user=None)

@app.route('/games')
@app.route('/games/')
def games_index():
    """Render the games index page with all available games"""
    games = [
        {
            'id': 'rock-paper-scissors',
            'name': 'Rock Paper Scissors',
            'description': 'Challenge the AI to a classic game of Rock Paper Scissors using hand gestures. Show your hand gesture to play!'
        },
        {
            'id': 'air-piano',
            'name': 'Air Piano',
            'description': 'Play a virtual piano in the air using your hand movements. Create music with simple hand gestures!'
        },
        {
            'id': 'maze-runner',
            'name': 'Maze Runner',
            'description': 'Navigate through challenging mazes using head movements. Tilt and turn to find your way to the exit!'
        },
        {
            'id': 'pong',
            'name': 'Gesture Pong',
            'description': 'Play the classic Pong game using hand gestures to control your paddle. Challenge the AI in this retro favorite!'
        },
        {
            'id': 'archery',
            'name': 'Virtual Archery',
            'description': 'Test your aim in this virtual archery game. Draw your bow with hand gestures and hit the targets!'
        },
        {
            'id': 'dance-mirror',
            'name': 'Dance Mirror',
            'description': 'Mirror the dance moves shown on screen using your whole body. Get your groove on and score points!'
        },
        {
            'id': 'face-race',
            'name': 'Face Race',
            'description': 'Race against time using facial expressions. Make the right faces to score points and beat the clock!'
        },
        {
            'id': 'math-quiz',
            'name': 'Math Gestures',
            'description': 'Solve math problems using finger counting and hand gestures. A fun way to practice mathematics!'
        },
        {
            'id': 'memory-tiles',
            'name': 'Memory Tiles',
            'description': 'Test your memory by matching tiles using hand gestures. Remember the patterns and find the pairs!'
        },
        {
            'id': 'whack-a-mole',
            'name': 'Gesture Whack-a-Mole',
            'description': 'Whack the moles using hand gestures in this classic arcade game reimagined with motion controls!'
        }
    ]
    return render_template('games/index.html', current_user=None, games=games)

@app.route('/games/<game_name>')
def play_game(game_name):
    """Handle individual game routes"""
    valid_games = [
        'rock-paper-scissors',
        'air-piano',
        'maze-runner',
        'pong',
        'archery',
        'dance-mirror',
        'face-race',
        'math-quiz',
        'memory-tiles',
        'whack-a-mole'
    ]
    
    if game_name not in valid_games:
        return redirect(url_for('games_index'))
    
    # Convert hyphenated game name to underscore format
    template_name = f'games/{game_name.replace("-", "_")}.html'
    
    try:
        # Add a back button to games index
        return render_template(template_name, 
                            current_user=None, 
                            game_name=game_name,
                            games_url=url_for('games_index'))
    except Exception as e:
        app.logger.error(f"Error loading template {template_name}: {str(e)}")
        return redirect(url_for('games_index'))

# Add a direct redirect from /rock-paper-scissors to games index
@app.route('/rock-paper-scissors')
def rps_redirect():
    return redirect(url_for('games_index'))

# Add a direct redirect from /air-piano to games index
@app.route('/air-piano')
def piano_redirect():
    return redirect(url_for('games_index'))

@app.route('/about')
def about():
    return render_template('about.html', current_user=None)

@app.route('/api/user/videos')
def get_user_videos():
    # Use a default user ID since we removed login
    default_user_id = "default_user"
    favorites = MovieFavorite.get_user_favorites(default_user_id)
    return jsonify({'videos': favorites})

def count_fingers(lst):
    """Count number of raised fingers with improved accuracy"""
    cnt = 0
    # Calculate adaptive threshold based on hand size
    hand_size = abs(lst.landmark[0].y - lst.landmark[9].y)
    thresh = hand_size * 0.4  # 40% of hand size
    
    # Improved finger detection with stricter thresholds
    if (lst.landmark[5].y - lst.landmark[8].y) > thresh and (lst.landmark[6].y - lst.landmark[8].y) > thresh * 0.7:
        cnt += 1
    if (lst.landmark[9].y - lst.landmark[12].y) > thresh and (lst.landmark[10].y - lst.landmark[12].y) > thresh * 0.7:
        cnt += 1
    if (lst.landmark[13].y - lst.landmark[16].y) > thresh and (lst.landmark[14].y - lst.landmark[16].y) > thresh * 0.7:
        cnt += 1
    if (lst.landmark[17].y - lst.landmark[20].y) > thresh and (lst.landmark[18].y - lst.landmark[20].y) > thresh * 0.7:
        cnt += 1
    # Improved thumb detection using x-coordinates and angle
    thumb_angle = calculate_angle(
        (lst.landmark[4].x, lst.landmark[4].y),
        (lst.landmark[3].x, lst.landmark[3].y),
        (lst.landmark[2].x, lst.landmark[2].y)
    )
    if thumb_angle > 150 and (lst.landmark[5].x - lst.landmark[4].x) > hand_size * 0.25:
        cnt += 1
    return cnt

def process_frame(frame, game_type):
    """Process a frame and return gesture data based on game type"""
    if frame is None:
        return None
    
    # Flip frame horizontally
    frame = cv2.flip(frame, 1)
    
    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    response_data = {
        'frame': frame,
        'timestamp': time.time(),
        'face_detected': False,
        'hand_detected': False
    }
    
    # Face detection using Haar Cascade
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    response_data['face_detected'] = len(faces) > 0
    
    # Face mesh detection
    face_results = face_mesh.process(rgb_frame)
    if face_results.multi_face_landmarks:
        face_landmarks = face_results.multi_face_landmarks[0]
        response_data['face_landmarks'] = [
            {'x': lm.x, 'y': lm.y, 'z': lm.z}
            for lm in face_landmarks.landmark
        ]
        
        # Draw face landmarks on frame
        drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=drawing_spec,
            connection_drawing_spec=drawing_spec
        )
    
    # Hand detection
    hand_results = hands.process(rgb_frame)
    if hand_results.multi_hand_landmarks:
        hand_landmarks = hand_results.multi_hand_landmarks[0]
        response_data['hand_detected'] = True
        response_data['hand_landmarks'] = [
            {'x': lm.x, 'y': lm.y, 'z': lm.z}
            for lm in hand_landmarks.landmark
        ]
        
        # Draw hand landmarks on frame
        mp_drawing.draw_landmarks(
            frame, 
            hand_landmarks, 
            mp_hands.HAND_CONNECTIONS
        )
        
        # Process specific game gestures
        if game_type == 'rps':
            response_data['gesture'] = detect_rps_gesture(hand_landmarks)
        elif game_type == 'piano':
            response_data['finger_positions'] = detect_piano_fingers(hand_landmarks)
        elif game_type == 'math':
            response_data['finger_count'] = count_fingers(hand_landmarks)
        
    return response_data

@app.route('/process_gesture', methods=['POST'])
def process_gesture():
        data = request.get_json()
    game_type = data.get('game_type')
    gesture_data = data.get('gesture_data')
    
    if not game_type or not gesture_data:
        return jsonify({'error': 'Missing game type or gesture data'}), 400
    
    # Process gestures based on game type
    if game_type == 'rps':
        return process_rps_gesture(gesture_data)
    elif game_type == 'piano':
        return process_piano_gesture(gesture_data)
    elif game_type == 'maze':
        return process_maze_gesture(gesture_data)
    elif game_type == 'pong':
        return process_pong_gesture(gesture_data)
    elif game_type == 'archery':
        return process_archery_gesture(gesture_data)
    elif game_type == 'dance':
        return process_dance_gesture(gesture_data)
    elif game_type == 'face':
        return process_face_gesture(gesture_data)
    elif game_type == 'math':
        return process_math_gesture(gesture_data)
    elif game_type == 'video':
        return process_video_gesture(gesture_data)
    else:
        return jsonify({'error': 'Invalid game type'}), 400

# Helper functions for processing game-specific gestures
def process_rps_gesture(data):
    gesture = data.get('gesture')
    if not gesture:
        return jsonify({'error': 'No gesture data provided'}), 400
        return jsonify({
        'gesture': gesture,
        'success': True
    })

def process_piano_gesture(data):
    finger_positions = data.get('finger_positions')
    if not finger_positions:
        return jsonify({'error': 'No finger position data provided'}), 400
    return jsonify({
        'finger_positions': finger_positions,
        'success': True
    })

def process_maze_gesture(data):
    head_tilt = data.get('head_tilt')
    if head_tilt is None:
        return jsonify({'error': 'No head tilt data provided'}), 400
    return jsonify({
        'head_tilt': head_tilt,
        'success': True
    })

def process_pong_gesture(data):
    hand_position = data.get('hand_position')
    if not hand_position:
        return jsonify({'error': 'No hand position data provided'}), 400
    return jsonify({
        'hand_position': hand_position,
        'success': True
    })

def process_archery_gesture(data):
    pull_back = data.get('pull_back')
    if pull_back is None:
        return jsonify({'error': 'No pull back data provided'}), 400
        return jsonify({
        'pull_back': pull_back,
        'success': True
    })

def process_dance_gesture(data):
    pose = data.get('pose')
    if not pose:
        return jsonify({'error': 'No pose data provided'}), 400
    return jsonify({
        'pose': pose,
        'success': True
    })

def process_face_gesture(data):
    expression = data.get('expression')
    if not expression:
        return jsonify({'error': 'No expression data provided'}), 400
    return jsonify({
        'expression': expression,
        'success': True
    })

def process_math_gesture(data):
    finger_count = data.get('finger_count')
    if finger_count is None:
        return jsonify({'error': 'No finger count data provided'}), 400
    return jsonify({
        'finger_count': finger_count,
        'success': True
    })

def process_video_gesture(data):
    gesture = data.get('gesture')
    if not gesture:
        return jsonify({'error': 'No gesture data provided'}), 400
    return jsonify({
        'gesture': gesture,
        'success': True
    })

@app.route('/api/favorites', methods=['GET'])
def fetch_user_favorites():
    # Use default user ID
    default_user_id = "default_user"
    favorites = MovieFavorite.get_user_favorites(default_user_id)
    return jsonify({
        'success': True,
        'favorites': favorites
    })

@app.route('/api/favorites/<video_id>', methods=['POST'])
def add_favorite(video_id):
    default_user_id = "default_user"
    video_data = request.get_json()
    if not video_data:
        result = get_video_details(video_id)
        if not result.get('success'):
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        video_data = result['video']
    
    success = MovieFavorite.add_favorite(default_user_id, video_id, video_data)
    return jsonify({
        'success': success,
        'message': 'Video added to favorites'
    })

@app.route('/api/favorites/<video_id>', methods=['DELETE'])
def remove_favorite(video_id):
    default_user_id = "default_user"
    success = MovieFavorite.remove_favorite(default_user_id, video_id)
    return jsonify({
        'success': success,
        'message': 'Video removed from favorites' if success else 'Video not found in favorites'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    default_user_id = "default_user"
    limit = request.args.get('limit', 20, type=int)
    history = MovieHistory.get_user_history(default_user_id, limit)
    return jsonify({
        'success': True,
        'history': history
    })

@app.route('/api/gesture/state', methods=['GET'])
def get_gesture_state():
    return jsonify({
        'enabled': gesture_control_enabled
    })

# Gesture detection functions
def detect_rps_gesture(hand_landmarks):
    """Detect Rock, Paper, Scissors gesture from hand landmarks"""
    # Get y-coordinates of fingertips and their corresponding MCP joints
    fingertip_y = [hand_landmarks.landmark[i].y for i in [8, 12, 16, 20]]  # Index, Middle, Ring, Pinky tips
    mcp_y = [hand_landmarks.landmark[i].y for i in [5, 9, 13, 17]]  # Corresponding MCP joints
    
    # Get thumb position
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    thumb_extended = thumb_tip.x < thumb_ip.x  # For right hand
    
    # Count extended fingers (excluding thumb)
    extended_fingers = sum(1 for tip_y, base_y in zip(fingertip_y, mcp_y) if tip_y < base_y)
    
    # Detect gestures based on finger positions
    if extended_fingers == 0 and not thumb_extended:
        return 'rock'
    elif extended_fingers == 4 and thumb_extended:
        return 'paper'
    elif extended_fingers == 2 and not thumb_extended:
        # Check if index and middle fingers are extended while others are closed
        if (fingertip_y[0] < mcp_y[0] and  # Index extended
            fingertip_y[1] < mcp_y[1] and  # Middle extended
            fingertip_y[2] > mcp_y[2] and  # Ring closed
            fingertip_y[3] > mcp_y[3]):    # Pinky closed
            return 'scissors'
    
        return None
    
def detect_piano_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
    finger_positions = []
    
    for tip in finger_tips:
        y_pos = hand_landmarks.landmark[tip].y
        base_y = hand_landmarks.landmark[tip - 2].y
        if y_pos < base_y:
            finger_positions.append({
                'finger': tip,
                'x': hand_landmarks.landmark[tip].x,
                'y': y_pos
            })
    
    return finger_positions

def detect_head_pose(face_landmarks, frame):
    h, w, _ = frame.shape
    nose = face_landmarks.landmark[1]
    left_eye = face_landmarks.landmark[33]
    right_eye = face_landmarks.landmark[263]
    
    nose_x = int(nose.x * w)
    left_x = int(left_eye.x * w)
    right_x = int(right_eye.x * w)
    
    head_tilt = (right_x - left_x) / w
    head_turn = (nose_x - w/2) / (w/2)
    
    return {
        'tilt': head_tilt,
        'turn': head_turn
    }

def detect_hand_position(hand_landmarks, frame):
    h, w, _ = frame.shape
    wrist = hand_landmarks.landmark[0]
    return {
        'x': wrist.x,
        'y': wrist.y,
        'relative_x': wrist.x * w / w,
        'relative_y': wrist.y * h / h
    }

def detect_archery_pose(pose_landmarks, frame):
    h, w, _ = frame.shape
    right_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    right_elbow = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
    right_wrist = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
    
    # Calculate angle between shoulder, elbow, and wrist
    angle = calculate_angle(
        (right_shoulder.x * w, right_shoulder.y * h),
        (right_elbow.x * w, right_elbow.y * h),
        (right_wrist.x * w, right_wrist.y * h)
    )
    
    draw_strength = 1 - (angle / 180)  # Normalize to 0-1 range
    return {
        'draw_strength': draw_strength,
        'angle': angle
    }

def detect_dance_pose(pose_landmarks, frame):
    h, w, _ = frame.shape
    # Get key pose points
    keypoints = {
        'left_shoulder': pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER],
        'right_shoulder': pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        'left_hip': pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP],
        'right_hip': pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP],
        'left_knee': pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE],
        'right_knee': pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE],
        'left_ankle': pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE],
        'right_ankle': pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
    }
    
    # Calculate body angles and positions
    pose_data = {
        'hip_shoulder_angle': calculate_angle(
            (keypoints['left_hip'].x * w, keypoints['left_hip'].y * h),
            (keypoints['left_shoulder'].x * w, keypoints['left_shoulder'].y * h),
            (keypoints['right_shoulder'].x * w, keypoints['right_shoulder'].y * h)
        ),
        'knee_hip_angle': calculate_angle(
            (keypoints['left_knee'].x * w, keypoints['left_knee'].y * h),
            (keypoints['left_hip'].x * w, keypoints['left_hip'].y * h),
            (keypoints['right_hip'].x * w, keypoints['right_hip'].y * h)
        )
    }
    
    return pose_data

def detect_face_expression(face_landmarks, frame):
    h, w, _ = frame.shape
    
    # Calculate key facial features
    left_eye = calculate_eye_aspect_ratio(face_landmarks, 'left', frame)
    right_eye = calculate_eye_aspect_ratio(face_landmarks, 'right', frame)
    mouth_open = calculate_mouth_aspect_ratio(face_landmarks, frame)
    
    # Determine expression
    if left_eye < 0.2 and right_eye < 0.2:
        return 'blink'
    elif mouth_open > 0.7:
        return 'open_mouth'
    elif left_eye > 0.25 and right_eye > 0.25:
        return 'surprise'
    return None

def calculate_angle(p1, p2, p3):
    """Calculate angle between three points"""
    angle = math.degrees(math.atan2(p3[1]-p2[1], p3[0]-p2[0]) - 
                        math.atan2(p1[1]-p2[1], p1[0]-p2[0]))
    return abs(angle)

def calculate_eye_aspect_ratio(landmarks, eye, frame):
    """Calculate the eye aspect ratio"""
    if eye == 'left':
        points = [(33, 160), (158, 144), (153, 145)]
    else:
        points = [(362, 386), (382, 398), (384, 381)]
    
    distances = []
    h, w, _ = frame.shape
    for p1, p2 in points:
        x1 = landmarks.landmark[p1].x * w
        y1 = landmarks.landmark[p1].y * h
        x2 = landmarks.landmark[p2].x * w
        y2 = landmarks.landmark[p2].y * h
        distances.append(math.dist((x1, y1), (x2, y2)))
    
    return sum(distances) / len(distances)

def calculate_mouth_aspect_ratio(landmarks, frame):
    """Calculate the mouth aspect ratio"""
    mouth_points = [(61, 291), (39, 181), (0, 17), (269, 405)]
    
    distances = []
    h, w, _ = frame.shape
    for p1, p2 in mouth_points:
        x1 = landmarks.landmark[p1].x * w
        y1 = landmarks.landmark[p1].y * h
        x2 = landmarks.landmark[p2].x * w
        y2 = landmarks.landmark[p2].y * h
        distances.append(math.dist((x1, y1), (x2, y2)))
    
    return sum(distances) / len(distances)

def detect_video_gestures(hand_landmarks, face_landmarks, face_detected):
    """Process gestures and return appropriate video control command"""
    global last_gesture_time
    current_time = time.time()
    
    # Throttle gesture detection
    if current_time - last_gesture_time < MIN_GESTURE_INTERVAL:
        return None
        
    # Process hand gestures first as they take priority
    if hand_landmarks:
        count = count_fingers(hand_landmarks)
        last_gesture_time = current_time
        
        # Map finger count to commands
        if count == 1:
            return "volumeup"
        elif count == 2:
            return "volumedown"
        elif count == 3:
            return "forward"
        elif count == 4:
            return "backward"
        elif count == 5:
            return "playpause"
    
    # Process face detection for auto-pause
    if not face_detected and current_time - last_gesture_time > 2:
        last_gesture_time = current_time
        return "pause"
    
    # Process head tilt if face landmarks are available
    if face_landmarks:
        # Calculate eye centers for head tilt detection
        left_eye = np.array([(face_landmarks.landmark[i].x, face_landmarks.landmark[i].y) 
                            for i in [33, 133, 159, 145]])
        right_eye = np.array([(face_landmarks.landmark[i].x, face_landmarks.landmark[i].y) 
                             for i in [362, 263, 386, 374]])
        
        eye_center_x = (left_eye[:, 0].mean() + right_eye[:, 0].mean()) / 2
        face_center_x = face_landmarks.landmark[1].x
        
        if eye_center_x - face_center_x > 0.05:
            return "seekforward"
        elif face_center_x - eye_center_x > 0.05:
            return "seekbackward"
    
    return None

@sock.route('/gesture_stream/video')
def video_gesture_stream(ws):
    """WebSocket route for video gesture controls with improved camera handling"""
    app.logger.info("Starting video gesture stream")
    
    # Try different camera indices
    camera_indices = [0, 1] if os.name == 'nt' else [0]  # Try both 0 and 1 on Windows
    cap = None
    
    for idx in camera_indices:
        try:
            if os.name == 'nt':
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(idx)
            
            if cap.isOpened():
                # Configure camera settings
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
                cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Set moderate brightness
                cap.set(cv2.CAP_PROP_CONTRAST, 128)  # Set moderate contrast
                
                # Verify camera works
                for _ in range(5):  # Try reading multiple frames
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        app.logger.info(f"Successfully initialized camera {idx}")
                        break
                else:
                    raise Exception("Camera not providing valid frames")
                break
            else:
                cap.release()
                cap = None
        except Exception as e:
            app.logger.error(f"Failed to initialize camera {idx}: {str(e)}")
            if cap is not None:
                cap.release()
                cap = None
            continue
    
    if cap is None:
        error_msg = "Failed to initialize any camera"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
        return

    # Initialize MediaPipe components with optimized settings
    try:
        hand_detector = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.6,  # Increased confidence threshold
            min_tracking_confidence=0.6,
            model_complexity=1  # Use balanced model
        )
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            refine_landmarks=True  # Enable landmark refinement for better accuracy
        )
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if face_cascade.empty():
            error_msg = "Failed to load face cascade classifier"
            app.logger.error(error_msg)
            ws.send(json.dumps({"error": error_msg}))
            return
            
        ws.send(json.dumps({"status": "Gesture control initialized successfully"}))
    except Exception as e:
        error_msg = f"Failed to initialize gesture detection: {str(e)}"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
        if cap is not None:
            cap.release()
        return
    
    frame_count = 0
    last_frame_time = time.time()
    fps_target = 30
    frame_interval = 1.0 / fps_target
    
    try:
        while True:
            current_time = time.time()
            if current_time - last_frame_time < frame_interval:
                time.sleep(0.001)  # Short sleep to prevent CPU overload
                continue
                
            success, frame = cap.read()
            if not success or frame is None or frame.size == 0:
                app.logger.warning("Failed to read frame from camera")
                # Try to recover camera
                cap.release()
                time.sleep(0.1)
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else None)
                continue

            frame_count += 1
            last_frame_time = current_time
            
            # Process every other frame to reduce CPU load
            if frame_count % 2 != 0:
                continue

            # Flip frame horizontally for more intuitive interaction
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces using Haar Cascade with optimized parameters
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            face_detected = len(faces) > 0
            
            # Process hand landmarks with error handling
            try:
                hand_results = hand_detector.process(rgb_frame)
                hand_landmarks = hand_results.multi_hand_landmarks[0] if hand_results.multi_hand_landmarks else None
    except Exception as e:
                app.logger.error(f"Error processing hand landmarks: {str(e)}")
                hand_landmarks = None
            
            # Process face landmarks with error handling
            try:
                face_results = face_mesh.process(rgb_frame)
                face_landmarks = face_results.multi_face_landmarks[0] if face_results.multi_face_landmarks else None
            except Exception as e:
                app.logger.error(f"Error processing face landmarks: {str(e)}")
                face_landmarks = None
            
            # Draw landmarks on frame for visualization
            if hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=(0, 200, 0), thickness=2))
            
            if face_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, face_landmarks, mp.solutions.face_mesh.FACEMESH_TESSELATION,
                    mp.solutions.drawing_utils.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=1),
                    mp.solutions.drawing_utils.DrawingSpec(color=(200, 200, 200), thickness=1))
            
            # Draw face detection rectangles
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Detect gestures and send commands
            command = detect_video_gestures(hand_landmarks, face_landmarks, face_detected)
            if command:
                app.logger.debug(f"Detected gesture command: {command}")
                ws.send(json.dumps({
                    'command': command,
                    'timestamp': time.time()
                }))
            
            # Encode frame for visualization with error handling
            try:
                # Resize frame to reduce bandwidth
                frame_small = cv2.resize(frame, (320, 240))
                _, buffer = cv2.imencode('.jpg', frame_small, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_data = base64.b64encode(buffer).decode('utf-8')
                
                # Send frame data for visualization
                ws.send(json.dumps({
                    'frame': frame_data,
                    'timestamp': time.time()
                }))
            except Exception as e:
                app.logger.error(f"Error encoding frame: {str(e)}")

    except Exception as e:
        error_msg = f"Video gesture stream error: {str(e)}"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
    finally:
        app.logger.info("Closing video gesture stream")
        hand_detector.close()
        face_mesh.close()
        if cap is not None:
            cap.release()

# WebSocket routes for each game
@sock.route('/gesture_stream/rps')
def rps_gesture_stream(ws):
    app.logger.info("Starting RPS gesture stream")
    
    # Initialize MediaPipe
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    # Initialize camera with DirectShow backend on Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        error_msg = "Failed to open camera"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
        return

    try:
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        while True:
            success, frame = cap.read()
            if not success:
                ws.send(json.dumps({"error": "Failed to read frame"}))
                continue

            # Flip the frame horizontally for a later selfie-view display
            frame = cv2.flip(frame, 1)
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and detect hands
            results = hands.process(rgb_frame)
            
            # Prepare the response data
            response_data = {"hands": []}
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Convert landmarks to list of coordinates
                    landmarks = []
                    for landmark in hand_landmarks.landmark:
                        landmarks.append({
                            "x": landmark.x,
                            "y": landmark.y,
                            "z": landmark.z
                        })
                    
                    # Detect RPS gesture using improved method
                    # Get fingertip and pip landmarks for each finger
                    thumb_tip = hand_landmarks.landmark[4]
                    thumb_ip = hand_landmarks.landmark[3]
                    thumb_mcp = hand_landmarks.landmark[2]
                    
                    index_tip = hand_landmarks.landmark[8]
                    index_pip = hand_landmarks.landmark[6]
                    
                    middle_tip = hand_landmarks.landmark[12]
                    middle_pip = hand_landmarks.landmark[10]
                    
                    ring_tip = hand_landmarks.landmark[16]
                    ring_pip = hand_landmarks.landmark[14]
                    
                    pinky_tip = hand_landmarks.landmark[20]
                    pinky_pip = hand_landmarks.landmark[18]
                    
                    # Calculate finger states
                    thumb_extended = thumb_tip.x < thumb_ip.x
                    index_extended = index_tip.y < index_pip.y
                    middle_extended = middle_tip.y < middle_pip.y
                    ring_extended = ring_tip.y < ring_pip.y
                    pinky_extended = pinky_tip.y < pinky_pip.y
                    
                    # Count extended fingers
                    extended_fingers = sum([
                        thumb_extended,
                        index_extended,
                        middle_extended,
                        ring_extended,
                        pinky_extended
                    ])
                    
                    # Determine gesture
                    gesture = None
                    if extended_fingers == 0:
                        gesture = "rock"
                    elif extended_fingers == 5:
                        gesture = "paper"
                    elif index_extended and middle_extended and not ring_extended and not pinky_extended:
                        gesture = "scissors"
                    
                    # Draw landmarks on frame for visualization
                    mp_drawing.draw_landmarks(
            frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(0, 200, 0), thickness=2)
                    )
                    
                    # Add hand data to response
                    response_data["hands"].append({
                        "landmarks": landmarks,
                        "gesture": gesture,
                        "finger_count": extended_fingers
                    })
            
            # Encode frame for visualization
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_data = base64.b64encode(buffer).decode('utf-8')
            response_data["frame"] = frame_data
            
            # Send the response
            ws.send(json.dumps(response_data))
            
            # Add a small delay to control frame rate
            time.sleep(0.033)  # ~30 fps
            
    except Exception as e:
        error_msg = f"Error in RPS gesture stream: {str(e)}"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
    finally:
        app.logger.info("Closing RPS gesture stream")
        cap.release()
        hands.close()

@sock.route('/gesture_stream/piano')
def piano_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    try:
    while True:
        success, frame = cap.read()
        if not success:
                continue
                
            result = process_frame(frame, 'piano')
            if result:
                ws.send(json.dumps({
                    'finger_positions': result.get('finger_positions'),
                    'landmarks': result.get('hand_landmarks'),
                    'timestamp': result['timestamp']
                }))
            
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Piano WebSocket error: {str(e)}")
    finally:
        cap.release()

@sock.route('/gesture_stream/maze')
def maze_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        error_msg = "Failed to open camera"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
        return
        
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue
                
            result = process_frame(frame, 'maze')
            if result and result.get('face_landmarks'):
                # Calculate head pose from face landmarks
                head_pose = detect_head_pose(result['face_landmarks'], frame)
                ws.send(json.dumps({
                    'head_pose': head_pose,
                    'landmarks': result.get('face_landmarks'),
                    'timestamp': result['timestamp']
                }))
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Maze WebSocket error: {str(e)}")
        ws.send(json.dumps({"error": str(e)}))
    finally:
        cap.release()

@sock.route('/gesture_stream/pong')
def pong_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            
            if results.multi_hand_landmarks:
                hand_position = detect_hand_position(results.multi_hand_landmarks[0], frame)
                if hand_position:
                    ws.send(json.dumps({
                        'hand_position': hand_position,
                        'timestamp': time.time()
                    }))
                    time.sleep(0.03)
            time.sleep(0.01)
        except Exception as e:
        app.logger.error(f"Pong WebSocket error: {str(e)}")
    finally:
        cap.release()

@sock.route('/gesture_stream/archery')
def archery_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        error_msg = "Failed to open camera"
        app.logger.error(error_msg)
        ws.send(json.dumps({"error": error_msg}))
        return
        
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            
            if results.pose_landmarks:
                archery_pose = detect_archery_pose(results.pose_landmarks, frame)
                if archery_pose:
                    ws.send(json.dumps({
                        'archery_pose': archery_pose,
                        'timestamp': time.time()
                    }))
                    time.sleep(0.05)
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Archery WebSocket error: {str(e)}")
        ws.send(json.dumps({"error": str(e)}))
    finally:
        cap.release()

@sock.route('/gesture_stream/dance')
def dance_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            
            if results.pose_landmarks:
                dance_pose = detect_dance_pose(results.pose_landmarks, frame)
                if dance_pose:
                    ws.send(json.dumps({
                        'dance_pose': dance_pose,
                        'timestamp': time.time()
                    }))
                    time.sleep(0.05)
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Dance WebSocket error: {str(e)}")
    finally:
        cap.release()

@sock.route('/gesture_stream/face')
def face_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image)
            
            if results.multi_face_landmarks:
                expression = detect_face_expression(results.multi_face_landmarks[0], frame)
                if expression:
                    ws.send(json.dumps({
                        'expression': expression,
                        'timestamp': time.time()
                    }))
                    time.sleep(0.05)
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Face Race WebSocket error: {str(e)}")
    finally:
        cap.release()

@sock.route('/gesture_stream/math')
def math_gesture_stream(ws):
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            
            if results.multi_hand_landmarks:
                finger_count = count_fingers(results.multi_hand_landmarks[0])
                if finger_count is not None:
                    ws.send(json.dumps({
                        'finger_count': finger_count,
                        'timestamp': time.time()
                    }))
                    time.sleep(0.1)
            time.sleep(0.01)
    except Exception as e:
        app.logger.error(f"Math Quiz WebSocket error: {str(e)}")
    finally:
        cap.release()

# YouTube API Routes
@app.route('/api/youtube/search')
def youtube_search():
    query = request.args.get('q', DEFAULT_SEARCH_QUERY)
    page_token = request.args.get('pageToken', '')
    
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': YOUTUBE_RESULTS_PER_PAGE,
        'key': YOUTUBE_API_KEY,
        'pageToken': page_token
    }
    
    response = requests.get(f'{YOUTUBE_API_BASE_URL}/search', params=params)
    return response.json()

@app.route('/api/youtube/trending')
def youtube_trending():
    page_token = request.args.get('pageToken', '')
    region_code = request.args.get('regionCode', 'US')
    
    params = {
        'part': 'snippet',
        'chart': 'mostPopular',
        'maxResults': YOUTUBE_RESULTS_PER_PAGE,
        'key': YOUTUBE_API_KEY,
        'pageToken': page_token,
        'regionCode': region_code
    }
    
    response = requests.get(f'{YOUTUBE_API_BASE_URL}/videos', params=params)
    return response.json()

@app.route('/api/youtube/videos/<video_id>/stats')
def youtube_video_stats(video_id):
    params = {
        'part': 'statistics,contentDetails',
                    'id': video_id,
        'key': YOUTUBE_API_KEY
    }
    
    response = requests.get(f'{YOUTUBE_API_BASE_URL}/videos', params=params)
        data = response.json()
        
    if 'items' in data and len(data['items']) > 0:
        video = data['items'][0]
        # Convert duration from ISO 8601 format
        video['contentDetails']['duration'] = str(isodate.parse_duration(video['contentDetails']['duration']))
        return video
    
    return {'error': 'Video not found'}, 404

@app.route('/api/youtube/channel/<channel_id>/avatar')
def youtube_channel_avatar(channel_id):
    params = {
        'part': 'snippet',
        'id': channel_id,
        'key': YOUTUBE_API_KEY
    }
    
    response = requests.get(f'{YOUTUBE_API_BASE_URL}/channels', params=params)
    data = response.json()
    
    if 'items' in data and len(data['items']) > 0:
        avatar_url = data['items'][0]['snippet']['thumbnails']['default']['url']
        return {'url': avatar_url}
    
    return {'error': 'Channel not found'}, 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic here
        # For now, just redirect to home
        session['username'] = username
        return redirect(url_for('index'))
        
    return render_template('login.html', current_user=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords don't match", current_user=None)
            
        # TODO: Add actual registration logic here
        # For now, just redirect to login
        return redirect(url_for('login'))
        
    return render_template('register.html', current_user=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)