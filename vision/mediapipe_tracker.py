import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:

    PLAYER1_COLOR = (255, 0, 0)
    PLAYER2_COLOR = (0, 0, 255)

    LANDMARK_RADIUS = 5
    LINE_THICKNESS = 2

    CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),        # Thumb
            (0,5),(5,6),(6,7),(7,8),        # Index
            (5,9),(9,10),(10,11),(11,12),   # Middle
            (9,13),(13,14),(14,15),(15,16), # Ring
            (13,17),(17,18),(18,19),(19,20),# Pinky
            (0,17)                          # Palm
        ]
    
    def __init__(self):

        self.BaseOptions = python.BaseOptions
        self.HandLandmarker = vision.HandLandmarker
        self.HandLandmarkerOptions = vision.HandLandmarkerOptions
        self.RunningMode = vision.RunningMode

        options = self.HandLandmarkerOptions(
            base_options=self.BaseOptions(
                model_asset_path="model/hand_landmarker.task"
            ),
            running_mode=self.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        self.detector = self.HandLandmarker.create_from_options(options)

    def process_frame(self, frame, timestamp):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.detector.detect_for_video(mp_image,timestamp)
        return result
    
    def get_player(self, hand):
        wrist = hand[0]
        if wrist.x < 0.5:
            return ("PLAYER 1",self.PLAYER1_COLOR)     
        return ("PLAYER 2",self.PLAYER2_COLOR)  

    def assign_players(self, result):

        players = {

            "PLAYER 1": None,

            "PLAYER 2": None

        }

        if not result.hand_landmarks:
            return players

        for hand in result.hand_landmarks:

            wrist = hand[0]

            if wrist.x < 0.5:
                players["PLAYER 1"] = hand

            else:
                players["PLAYER 2"] = hand

        return players        
    
   
            