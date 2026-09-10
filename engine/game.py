
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
        self.game_over = False
        self.winner = ""
        self.game_over_time = 0.0


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
            pw1_x=35
            # --- Player 1 Stats ---
            # HP Bar
            cv2.putText(frame, "HP:", (pw1_x-30, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            cv2.rectangle(frame, (pw1_x, 50), (pw1_x+200, 65), (50, 50, 50), -1)
            cv2.rectangle(frame, (pw1_x, 50), (pw1_x + int(self.player1.health * 2), 65), (0, 200, 0), -1)
            cv2.rectangle(frame, (pw1_x, 50), (pw1_x+200, 65), (255, 255, 255), 1)
            cv2.putText(frame, f"{int(self.player1.health)} / 100", (pw1_x+210, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # MP Bar
            cv2.putText(frame, "MP:", (pw1_x-30, 87), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
            cv2.rectangle(frame, (pw1_x, 75), (pw1_x+200, 90), (50, 50, 50), -1)
            cv2.rectangle(frame, (pw1_x, 75), (pw1_x + int(self.player1.mana * 2), 90), (255, 100, 0), -1)
            cv2.rectangle(frame, (pw1_x, 75), (pw1_x+200, 90), (255, 255, 255), 1)
            cv2.putText(frame, f"{int(self.player1.mana)} / 100", (pw1_x+210, 87), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if not self.player1.is_defeated:
                if self.player1.spell_state == "CHARGING" and self.player1.locked_spell:
                    color = (0,255,0) if self.player1.mana >= self.player1.locked_spell.mana_cost else (0,165,255)
                    power = int((self.player1.charge_time / 5.0) * 100)
                    cv2.putText(frame, f"{self.player1.locked_spell.name}", (pw1_x,130), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 2)
                    cv2.putText(frame, f"Charging: {self.player1.charge_time:.1f}s / 5.0s", (pw1_x,165), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 1)
                    cv2.putText(frame, f"Power: {power}%", (pw1_x,200), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 1)
                    cv2.putText(frame, f"Cost: {self.player1.locked_spell.mana_cost} MP", (pw1_x,235), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
                elif self.player1.spell_state in ["CAST", "CANCELLED"]:
                    lines = self.player1.ui_message.split('\n')
                    color = (0,255,0) if self.player1.spell_state == "CAST" else (0,0,255)
                    for idx, line in enumerate(lines):
                        cv2.putText(frame, line, (pw1_x,130 + idx*35), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 2)
                
            # --- Player 2 Stats ---
            p2_x = w //2 
            cv2.putText(
                frame,
                "PLAYER 2",
                (p2_x, 35),
                cv2.FONT_HERSHEY_COMPLEX,
                0.8,
                (0,0,255),
                2 
            )
            
            # HP Bar
            cv2.putText(frame, "HP:", (p2_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            cv2.rectangle(frame, (p2_x + 40, 50), (p2_x + 240, 65), (50, 50, 50), -1)
            cv2.rectangle(frame, (p2_x + 40, 50), (p2_x + 40 + int(self.player2.health * 2), 65), (0, 200, 0), -1)
            cv2.rectangle(frame, (p2_x + 40, 50), (p2_x + 240, 65), (255, 255, 255), 1)
            cv2.putText(frame, f"{int(self.player2.health)} / 100", (p2_x + 250, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # MP Bar
            cv2.putText(frame, "MP:", (p2_x, 87), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
            cv2.rectangle(frame, (p2_x + 40, 75), (p2_x + 240, 90), (50, 50, 50), -1)
            cv2.rectangle(frame, (p2_x + 40, 75), (p2_x + 40 + int(self.player2.mana * 2), 90), (255, 100, 0), -1)
            cv2.rectangle(frame, (p2_x + 40, 75), (p2_x + 240, 90), (255, 255, 255), 1)
            cv2.putText(frame, f"{int(self.player2.mana)} / 100", (p2_x + 250, 87), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if not self.player2.is_defeated:
                if self.player2.spell_state == "CHARGING" and self.player2.locked_spell:
                    color = (0,255,0) if self.player2.mana >= self.player2.locked_spell.mana_cost else (0,165,255)
                    power = int((self.player2.charge_time / 5.0) * 100)
                    cv2.putText(frame, f"{self.player2.locked_spell.name}", (p2_x + 40,130), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 2)
                    cv2.putText(frame, f"Charging: {self.player2.charge_time:.1f}s / 5.0s", (p2_x + 40,165), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 1)
                    cv2.putText(frame, f"Power: {power}%", (p2_x + 40,200), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 1)
                    cv2.putText(frame, f"Cost: {self.player2.locked_spell.mana_cost} MP", (p2_x + 40,235), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
                elif self.player2.spell_state in ["CAST", "CANCELLED"]:
                    lines = self.player2.ui_message.split('\n')
                    color = (0,255,0) if self.player2.spell_state == "CAST" else (0,0,255)
                    for idx, line in enumerate(lines):
                        cv2.putText(frame, line, (p2_x + 40,130 + idx*35), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 2)

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

            # Mana Regeneration
            if not self.game_over:
                MANA_REGEN_RATE = 5.0 # 5 MP per second
                self.player1.restore_mana(MANA_REGEN_RATE * delta_time)
                self.player2.restore_mana(MANA_REGEN_RATE * delta_time)

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

            if not self.game_over:
                # Update Player 1 Spell State
                self.player1.update_spell_state(delta_time, p1_gesture, self.player2, self.spell_manager)

                # Update Player 2 Spell State
                self.player2.update_spell_state(delta_time, p2_gesture, self.player1, self.spell_manager)


            # ---------------- DRAW ---------------- #

            frame = self.hand_tracker.draw_connections(
                frame,
                hand_result
            )

            frame = self.hand_tracker.draw_landmarks(
                frame,
                hand_result
            )

            # ---------------- GAME OVER CHECK ---------------- #
            
            if not self.game_over:
                if self.player1.is_defeated:
                    self.game_over = True
                    self.winner = "PLAYER 2"
                    self.game_over_time = time.time()
                elif self.player2.is_defeated:
                    self.game_over = True
                    self.winner = "PLAYER 1"
                    self.game_over_time = time.time()
                    
            if self.game_over:
                text = f"{self.winner} WINS!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 2, 5)[0]
                text_x = (width - text_size[0]) // 2
                text_y = height // 2
                
                # Draw black background rectangle for text
                cv2.rectangle(frame, (text_x - 20, text_y - text_size[1] - 20), 
                              (text_x + text_size[0] + 20, text_y + 20), (0, 0, 0), -1)
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 215, 255), 5)
                
                if time.time() - self.game_over_time > 4.0:
                    break

            # ---------------- UI ---------------- #

            frame = self.display_text(frame)
            frame = self.display_fps(frame, delta_time)
            frame = self.divide_frame(frame)

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.camera.release_camera()