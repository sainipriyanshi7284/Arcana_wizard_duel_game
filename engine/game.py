import cv2
import time
import math

from vision.camera import Camera
from vision.mediapipe_tracker import HandTracker
from vision.gesture_recognizer import GestureRecognizer
from combat.player import Player
from spells.spell_manager import SpellManager
from engine.ui import FantasyHUD
from effects.spells_vfx import (
    FireVFX, IceVFX, ShieldVFX, LightningVFX, WindVFX, ProjectileManager
)


class Game:

    def __init__(self):
        self.camera = Camera()
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.player1 = Player("PLAYER 1", "LEFT")
        self.player2 = Player("PLAYER 2", "RIGHT")
        self.spell_manager = SpellManager()
        self.hud = FantasyHUD()

        # Visual Effects for Player 1
        self.p1_vfx = {
            "Closed_Fist": FireVFX(),
            "Victory": IceVFX(),
            "Open_Palm": ShieldVFX(),
            "Pointing_Up": LightningVFX(),
            "Thumb_Up": WindVFX(),
        }

        # Visual Effects for Player 2
        self.p2_vfx = {
            "Closed_Fist": FireVFX(),
            "Victory": IceVFX(),
            "Open_Palm": ShieldVFX(),
            "Pointing_Up": LightningVFX(),
            "Thumb_Up": WindVFX(),
        }

        self.projectiles = ProjectileManager()
        self.prev_p1_state = "IDLE"
        self.prev_p2_state = "IDLE"

        self.prev_time = time.time()
        self.start_time = time.time()
        self.last_timestamp = 0
        self.game_over = False
        self.winner = ""
        self.game_over_time = 0.0

    def _get_gesture_theme(self, gesture):
        themes = {
            "Closed_Fist": ("Fire", "Closed Fist", "fire"),
            "Victory": ("Ice", "Victory", "ice"),
            "Open_Palm": ("Shield", "Open Palm", "shield"),
            "Pointing_Up": ("Lightning", "Pointing Up", "lightning"),
            "Thumb_Up": ("Wind", "Thumb Up", "wind"),
        }
        return themes.get(gesture, (None, None, None))

    def run(self):
        if not self.camera.open_camera():
            return

        width, height = self.camera.get_dimensions()
        print(f"Camera Resolution : {width} x {height}")

        cv2.namedWindow("ARCANA", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("ARCANA", width, height)
        cv2.setWindowProperty("ARCANA", cv2.WND_PROP_TOPMOST, 1)

        while True:
            current_time = time.time()
            delta_time = current_time - self.prev_time
            self.prev_time = current_time

            # Mana Regeneration
            if not self.game_over:
                MANA_REGEN_RATE = 5.0  # 5 MP per second
                self.player1.restore_mana(MANA_REGEN_RATE * delta_time)
                self.player2.restore_mana(MANA_REGEN_RATE * delta_time)

            frame = self.camera.get_frame()
            if frame is None:
                break

            frame = cv2.flip(frame, 1)

            # Ensure strictly increasing timestamp for MediaPipe
            timestamp = int(time.time() * 1000)
            if timestamp <= self.last_timestamp:
                timestamp = self.last_timestamp + 1
            self.last_timestamp = timestamp

            # ---------------- DETECTION ---------------- #
            hand_result = self.hand_tracker.process_frame(frame, timestamp)
            players = self.hand_tracker.assign_players(hand_result)

            self.player1.update_hand(players["PLAYER 1"])
            self.player2.update_hand(players["PLAYER 2"])

            gesture_result = self.gesture_recognizer.recognize(frame, timestamp)

            p1_gesture = "None"
            p2_gesture = "None"

            if gesture_result.gestures and gesture_result.hand_landmarks:
                for i, hand_gestures in enumerate(gesture_result.gestures):
                    if hand_gestures:
                        gesture_name = hand_gestures[0].category_name
                        score = hand_gestures[0].score
                        hand_lms = gesture_result.hand_landmarks[i]
                        wrist = hand_lms[0]
                        assigned_player = "PLAYER 1" if wrist.x < 0.5 else "PLAYER 2"

                        if score > 0.4:
                            if assigned_player == "PLAYER 1":
                                p1_gesture = gesture_name
                            else:
                                p2_gesture = gesture_name

            # Hand points and centers for whole-hand visual effect anchoring
            h_f, w_f = frame.shape[:2]
            p1_hand = players["PLAYER 1"]
            p2_hand = players["PLAYER 2"]
            p1_pts = [(int(lm.x * w_f), int(lm.y * h_f)) for lm in p1_hand] if p1_hand else None
            p2_pts = [(int(lm.x * w_f), int(lm.y * h_f)) for lm in p2_hand] if p2_hand else None
            p1_pos = self.hand_tracker.get_hand_center(p1_hand, frame.shape)
            p2_pos = self.hand_tracker.get_hand_center(p2_hand, frame.shape)

            # ---------------- GAMEPLAY & SPELL STATE ---------------- #
            if not self.game_over:
                self.player1.update_spell_state(delta_time, p1_gesture, self.player2, self.spell_manager)
                self.player2.update_spell_state(delta_time, p2_gesture, self.player1, self.spell_manager)

                # Projectile trigger on cast
                if self.prev_p1_state != "CAST" and self.player1.spell_state == "CAST":
                    start_pt = p1_pos if p1_pos else (int(width * 0.25), int(height * 0.5))
                    target_pt = p2_pos if p2_pos else (int(width * 0.75), int(height * 0.5))
                    s_name = self.player1.locked_spell.name if self.player1.locked_spell else "Fireball"
                    self.projectiles.spawn(start_pt, target_pt, s_name, 30)

                if self.prev_p2_state != "CAST" and self.player2.spell_state == "CAST":
                    start_pt = p2_pos if p2_pos else (int(width * 0.75), int(height * 0.5))
                    target_pt = p1_pos if p1_pos else (int(width * 0.25), int(height * 0.5))
                    s_name = self.player2.locked_spell.name if self.player2.locked_spell else "Ice Blast"
                    self.projectiles.spawn(start_pt, target_pt, s_name, 30)

                self.prev_p1_state = self.player1.spell_state
                self.prev_p2_state = self.player2.spell_state

            # ---------------- UPDATE VFX ---------------- #
            p1_charge_ratio = min(1.0, self.player1.charge_time / 5.0)
            p2_charge_ratio = min(1.0, self.player2.charge_time / 5.0)

            # Update Player 1 VFX (Whole Hand)
            for g_name, vfx in self.p1_vfx.items():
                is_active = (p1_gesture == g_name or self.player1.locked_gesture == g_name) and (p1_pts is not None)
                vfx.update(delta_time, p1_pts, is_active=is_active, charge_ratio=p1_charge_ratio)

            # Update Player 2 VFX (Whole Hand)
            for g_name, vfx in self.p2_vfx.items():
                is_active = (p2_gesture == g_name or self.player2.locked_gesture == g_name) and (p2_pts is not None)
                vfx.update(delta_time, p2_pts, is_active=is_active, charge_ratio=p2_charge_ratio)

            self.projectiles.update(delta_time)

            # ---------------- DRAWING ---------------- #
            active_p1_gesture = self.player1.locked_gesture if self.player1.locked_gesture != "None" else p1_gesture
            active_p2_gesture = self.player2.locked_gesture if self.player2.locked_gesture != "None" else p2_gesture

            p1_theme = "fire" if (active_p1_gesture == "Closed_Fist") else ("ice" if active_p1_gesture == "Victory" else "neutral")
            p2_theme = "fire" if (active_p2_gesture == "Closed_Fist") else ("ice" if active_p2_gesture == "Victory" else "neutral")
            themes = {"PLAYER 1": p1_theme, "PLAYER 2": p2_theme}

            # 1. Themed Elemental Backgrounds (Fire Realm on left, Frost Realm on right)
            self.hud.draw_elemental_backgrounds(frame, delta_time)

            # 2. Themed magical hand skeletons
            frame = self.hand_tracker.draw_connections(frame, hand_result, player_themes=themes)
            frame = self.hand_tracker.draw_landmarks(frame, hand_result, player_themes=themes)

            # 3. Draw active spell VFX covering the whole hand (maximum color vibrancy!)
            if active_p1_gesture in self.p1_vfx and p1_pts is not None:
                self.p1_vfx[active_p1_gesture].draw(frame, p1_pts, charge_ratio=p1_charge_ratio)

            if active_p2_gesture in self.p2_vfx and p2_pts is not None:
                self.p2_vfx[active_p2_gesture].draw(frame, p2_pts, charge_ratio=p2_charge_ratio)

            # 4. Draw projectiles & impact explosions
            self.projectiles.draw(frame)

            # 5. Ornate Fantasy UI
            self.hud.draw_vignette(frame)
            self.hud.draw_center_divider(frame)
            self.hud.draw_header(frame)
            self.hud.draw_player_hud(frame, self.player1, self.player2)
            self.hud.draw_fps(frame, delta_time)


            # 5. Bottom Spell Badges / Cards
            card_bot_y = height - 30

            # Player 1 Spell Card
            if active_p1_gesture in self.p1_vfx:
                s_name, g_desc, theme = self._get_gesture_theme(active_p1_gesture)
                if s_name:
                    self.hud.draw_spell_card(frame, center_x=int(width * 0.22), bottom_y=card_bot_y,
                                            spell_name=s_name, gesture_name=g_desc, theme=theme)

            # Player 2 Spell Card
            if active_p2_gesture in self.p2_vfx:
                s_name, g_desc, theme = self._get_gesture_theme(active_p2_gesture)
                if s_name:
                    self.hud.draw_spell_card(frame, center_x=int(width * 0.78), bottom_y=card_bot_y,
                                            spell_name=s_name, gesture_name=g_desc, theme=theme)

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
                self.hud.draw_text_pil(frame, text, (width // 2, height // 2 - 20),
                                      font_size=36, color=(100, 220, 255), bold=True, center=True)
                if time.time() - self.game_over_time > 4.0:
                    break

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.camera.release_camera()