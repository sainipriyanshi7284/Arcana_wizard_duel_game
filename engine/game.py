import cv2
import time

from vision.camera import Camera
from vision.mediapipe_tracker import HandTracker
from vision.gesture_recognizer import GestureRecognizer
from combat.player import Player
from spells.spell_manager import SpellManager


class Game:

    def __init__(self):
        self.camera = Camera()
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.player1 = Player("PLAYER 1", "LEFT")
        self.player2 = Player("PLAYER 2", "RIGHT")
        self.spell_manager = SpellManager()
        self.prev_time = time.time()
        self.start_time = time.time()


    def display_text(self, frame):

        if time.time() - self.start_time < 5:

            cv2.putText(
                frame,
                "WELCOME TO ARCANA",
                (170, 50),
                cv2.FONT_HERSHEY_COMPLEX,
                1,
                (0,0,255),
                3
            )

        cv2.putText(
            frame,
            "PRESS Q TO QUIT",
            (10,470),
            cv2.FONT_HERSHEY_COMPLEX_SMALL,
            0.7,
            (0,0,255),
            1
        )

        return frame


    def display_fps(self, frame):

        current = time.time()

        fps = 1/(current-self.prev_time)

        self.prev_time = current

        cv2.putText(
            frame,
            f"FPS : {int(fps)}",
            (560,30),
            cv2.FONT_HERSHEY_COMPLEX_SMALL,
            0.8,
            (0,255,0),
            2
        )

        return frame


    def divide_frame(self, frame):

        h, w, _ = frame.shape

        if time.time()-self.start_time > 5:

            cv2.line(
                frame,
                (w//2,0),
                (w//2,h),
                (255,255,255),
                2
            )

            cv2.putText(
                frame,
                "PLAYER 1",
                (70,35),
                cv2.FONT_HERSHEY_COMPLEX,
                0.8,
                (255,0,0),
                2
            )

            cv2.putText(
                frame,
                "PLAYER 2",
                (w-220,35),
                cv2.FONT_HERSHEY_COMPLEX,
                0.8,
                (0,0,255),
                2
            )

        return frame


    def run(self):

        if not self.camera.open_camera():
            return

        width, height = self.camera.get_dimensions()

        print(f"Camera Resolution : {width} x {height}")

        while True:

            frame = self.camera.get_frame()

            if frame is None:
                break

            frame = cv2.flip(frame,1)

            timestamp = int(time.time()*1000)

            # ---------------- DETECTION ---------------- #

            hand_result = self.hand_tracker.process_frame(
                frame,
                timestamp
            )

            players = self.hand_tracker.assign_players(hand_result)

            self.player1.update_hand(players["PLAYER 1"])

            self.player2.update_hand(players["PLAYER 2"])
            gesture_result = self.gesture_recognizer.recognize(
                frame,
                timestamp
            )

            # ---------------- DRAW ---------------- #

            frame = self.hand_tracker.draw_connections(
                frame,
                hand_result
            )

            frame = self.hand_tracker.draw_landmarks(
                frame,
                hand_result
            )

            gesture_result = self.gesture_recognizer.recognize(
            frame,
            timestamp
        )

            # ---------------- UI ---------------- #

            frame = self.display_text(frame)

            frame = self.display_fps(frame)

            frame = self.divide_frame(frame)

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

        self.camera.release_camera()