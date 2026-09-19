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
    
    def get_hand_center(self, hand, frame_shape):
        """
        Computes the pixel coordinates (x, y) of the palm center from hand landmarks.
        """
        if not hand:
            return None
        h, w = frame_shape[:2]
        # Average key palm landmarks: wrist(0), index_mcp(5), middle_mcp(9), ring_mcp(13), pinky_mcp(17)
        palm_indices = [0, 5, 9, 13, 17]
        avg_x = sum(hand[i].x for i in palm_indices) / len(palm_indices)
        avg_y = sum(hand[i].y for i in palm_indices) / len(palm_indices)
        return int(avg_x * w), int(avg_y * h)

    def draw_landmarks(self, frame, result, player_themes=None):
        if not result.hand_landmarks:
            return frame

        h, w, _ = frame.shape
        for hand in result.hand_landmarks:
            player, _ = self.get_player(hand)
            theme = player_themes.get(player, "neutral") if player_themes else "neutral"

            # When an elemental spell is active, do NOT draw artificial dots over the fire/ice
            if theme in ["fire", "ice"]:
                continue

            for landmark in hand:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 5, (190, 190, 210), 1, cv2.LINE_AA)
                cv2.circle(frame, (x, y), 3, (255, 255, 255), -1, cv2.LINE_AA)
        return frame

    def draw_connections(self, frame, result, player_themes=None):
        if not result.hand_landmarks:
            return frame
        h, w, _ = frame.shape

        for hand in result.hand_landmarks:
            player, _ = self.get_player(hand)
            theme = player_themes.get(player, "neutral") if player_themes else "neutral"

            # When an elemental spell is active, do NOT draw artificial lines over the fire/ice
            if theme in ["fire", "ice"]:
                continue

            for start, end in self.CONNECTIONS:
                x1 = int(hand[start].x * w)
                y1 = int(hand[start].y * h)
                x2 = int(hand[end].x * w)
                y2 = int(hand[end].y * h)

                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1, cv2.LINE_AA)

        return frame



            