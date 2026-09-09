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
        self.last_timestamp = 0


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


    def display_fps(self, frame, delta_time):
        fps = 1 / delta_time if delta_time > 0 else 0
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
            
            # Display Player 1 Spell Name
            if self.player1.spell:
                cv2.putText(
                    frame,
                    f"Spell: {self.player1.spell.name}",
                    (70,70),
                    cv2.FONT_HERSHEY_COMPLEX,
                    0.6,
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
            
            # Display Player 2 Spell Name
            if self.player2.spell:
                cv2.putText(
                    frame,
                    f"Spell: {self.player2.spell.name}",
                    (w-220,70),
                    cv2.FONT_HERSHEY_COMPLEX,
                    0.6,
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
            current_time = time.time()
            delta_time = current_time - self.prev_time
            self.prev_time = current_time

            frame = self.camera.get_frame()

            if frame is None:
                break

            frame = cv2.flip(frame,1)

            # Ensure strictly increasing timestamp for MediaPipe
            timestamp = int(time.time()*1000)
            if timestamp <= self.last_timestamp:
                timestamp = self.last_timestamp + 1
            self.last_timestamp = timestamp

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

            # Assign gestures to players
            p1_gesture = "None"
            p2_gesture = "None"

            if gesture_result.gestures and gesture_result.hand_landmarks:
                num_hands = len(gesture_result.gestures)
                print(f"\n--- Detected {num_hands} hand(s) ---")
                
                for i, hand_gestures in enumerate(gesture_result.gestures):
                    if hand_gestures:
                        gesture_name = hand_gestures[0].category_name
                        score = hand_gestures[0].score
                        hand_lms = gesture_result.hand_landmarks[i]
                        wrist = hand_lms[0]
                        
                        assigned_player = "PLAYER 1" if wrist.x < 0.5 else "PLAYER 2"
                        
                        # Debug Print
                        print(f"Hand {i+1}: {gesture_name} (Confidence: {score:.2f}) | Wrist X: {wrist.x:.2f} -> {assigned_player}")

                        # Only use the gesture if confidence is decent
                        if score > 0.4:
                            if assigned_player == "PLAYER 1":
                                p1_gesture = gesture_name
                            else:
                                p2_gesture = gesture_name

            # Update Player 1 Spell State
            if p1_gesture != self.player1.gesture:
                self.player1.update_gesture(p1_gesture)
                if p1_gesture != "None" and p1_gesture != "":
                    self.player1.update_spell(self.spell_manager.get_spell(p1_gesture))
                else:
                    self.player1.update_spell(None)

            # Update Player 2 Spell State
            if p2_gesture != self.player2.gesture:
                self.player2.update_gesture(p2_gesture)
                if p2_gesture != "None" and p2_gesture != "":
                    self.player2.update_spell(self.spell_manager.get_spell(p2_gesture))
                else:
                    self.player2.update_spell(None)


            # ---------------- DRAW ---------------- #

            frame = self.hand_tracker.draw_connections(
                frame,
                hand_result
            )

            frame = self.hand_tracker.draw_landmarks(
                frame,
                hand_result
            )

            # ---------------- UI ---------------- #

            frame = self.display_text(frame)
            frame = self.display_fps(frame, delta_time)
            frame = self.divide_frame(frame)

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.camera.release_camera()