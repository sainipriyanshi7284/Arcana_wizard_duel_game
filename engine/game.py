import cv2
import time
import numpy as np
import random
import math
import os
from PIL import Image, ImageDraw, ImageFont

from vision.camera import Camera
from vision.mediapipe_tracker import HandTracker
from vision.gesture_recognizer import GestureRecognizer
from combat.player import Player
from spells.spell_manager import SpellManager
from effects.fire_vfx import FireVFX
from effects.ice_vfx import IceVFX
from effects.shield_vfx import ShieldVFX
from effects.lightning_vfx import LightningVFX
from effects.wind_vfx import WindVFX
from combat.spell_projectile import SpellProjectile

class AmbientParticles:
    def __init__(self, count, width, height):
        self.width = width
        self.height = height
        self.particles = np.zeros((count, 9))
        self.particles[:, 0] = np.random.uniform(0, width, count)
        self.particles[:, 1] = np.random.uniform(0, height, count)
        self.particles[:, 2] = np.random.uniform(1, 3, count)
        self.particles[:, 3] = np.random.uniform(-1.5, -0.2, count) # moving up
        self.particles[:, 4] = np.random.uniform(0.5, 1.0, count)
        self.particles[:, 5] = np.random.uniform(0, 2*math.pi, count)
        self.particles[:, 6] = 255 # B
        self.particles[:, 7] = 200 # G
        self.particles[:, 8] = 100 # R
        
    def draw(self, frame, time_sec, p1_color, p2_color):
        self.particles[:, 1] += self.particles[:, 3]
        
        # Slower horizontal drift
        self.particles[:, 0] += np.sin(self.particles[:, 5] + time_sec) * 0.5
        
        reset_idx = self.particles[:, 1] < 0
        self.particles[reset_idx, 1] = self.height
        self.particles[reset_idx, 0] = np.random.uniform(0, self.width, np.sum(reset_idx))
        
        overlay = np.zeros_like(frame)
        cx = self.width / 2
        
        for p in self.particles:
            x, y, size, _, glow, phase, b, g, r = p
            pulse = (math.sin(time_sec * 3 + phase) + 1) * 0.5
            
            # Determine target color based on screen side
            tb, tg, tr = p1_color if x < cx else p2_color
            
            # Lerp current color towards target color
            b += (tb - b) * 0.05
            g += (tg - g) * 0.05
            r += (tr - r) * 0.05
            
            # Save back to array
            p[6], p[7], p[8] = b, g, r
            
            core_size = int(size)
            aura_size = int(size * 4 + pulse * 2)
            
            color = (int(b), int(g), int(r))
            aura_color = (int(b*0.5), int(g*0.5), int(r*0.5))
            
            # Soft aura
            cv2.circle(overlay, (int(x), int(y)), aura_size, aura_color, -1)
            # Bright core
            cv2.circle(overlay, (int(x), int(y)), core_size, (255, 255, 255), -1)
            
        # Blur the aura slightly
        cv2.GaussianBlur(overlay, (11, 11), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        return frame


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
        
        self.fire_vfx = FireVFX()
        self.ice_vfx = IceVFX()
        self.shield_vfx = ShieldVFX()
        self.lightning_vfx = LightningVFX()
        self.wind_vfx = WindVFX()
        self.projectiles = []
        
        self.p1_prev_state = "IDLE"
        self.p2_prev_state = "IDLE"
        self.ambient = None
        
        # UI Assets
        self.font_title = None
        self.font_ui = None
        self.parchment_img = None
        
        self.load_ui_assets()

    def load_ui_assets(self):
        # Try loading Harry Potter style font (Old English)
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 40)
            self.font_ui = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 24)
            self.font_small = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 18)
        except:
            self.font_title = ImageFont.load_default()
            self.font_ui = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
        # Load parchment texture
        parchment_path = r"C:\Users\hp\.gemini\antigravity-ide\brain\545a6b13-6c80-457f-9b3c-5fdbf191a295\parchment_ui_panel_1789832035219.jpg"
        if os.path.exists(parchment_path):
            try:
                # Load and resize for spell panel (width=250, height=80)
                img = Image.open(parchment_path).convert("RGBA")
                # Make it semi-transparent
                alpha = img.split()[3]
                alpha = alpha.point(lambda p: int(p * 0.85)) # 85% opacity
                img.putalpha(alpha)
                self.parchment_img = img.resize((250, 80))
            except Exception as e:
                print("Failed to load parchment:", e)


    def get_spell_color(self, spell_name, default_color):
        if spell_name == "Fireball":
            return (0, 165, 255) # Orange
        elif spell_name == "Ice Blast":
            return (255, 200, 50) # Cyan-blue
        elif spell_name == "Shield":
            return (0, 255, 255) # Yellow
        elif spell_name == "Lightning":
            return (255, 0, 255) # Purple
        elif spell_name == "Wind Slash":
            return (200, 200, 200) # White
        return default_color

    def draw_star(self, frame, x, y, size, color):
        pts = np.array([
            [x, y - size],
            [x + int(size/3), y - int(size/3)],
            [x + size, y],
            [x + int(size/3), y + int(size/3)],
            [x, y + size],
            [x - int(size/3), y + int(size/3)],
            [x - size, y],
            [x - int(size/3), y - int(size/3)]
        ], np.int32)
        cv2.fillPoly(frame, [pts], color)

    def draw_ui_base(self, frame, w, h):
        # 1. Center Divider (Ornate Gold)
        cx = w // 2
        gold = (50, 170, 255) # BGR
        cv2.line(frame, (cx, 0), (cx, h), gold, 1)
        
        # Draw stars on the divider
        self.draw_star(frame, cx, h//2, 10, gold)
        self.draw_star(frame, cx, 20, 10, gold)
        self.draw_star(frame, cx, h - 20, 10, gold)
        
        # 2. Draw Player 1 UI (Top Left)
        p1_x = 20
        p1_y = 30
        
        # HP Bar (Red)
        cv2.rectangle(frame, (p1_x, p1_y + 10), (p1_x + 150, p1_y + 22), (0, 0, 50), -1)
        hp1_w = int((self.player1.health / 100) * 150)
        cv2.rectangle(frame, (p1_x, p1_y + 10), (p1_x + hp1_w, p1_y + 22), (50, 50, 200), -1)
        cv2.rectangle(frame, (p1_x, p1_y + 10), (p1_x + 150, p1_y + 22), (100, 100, 255), 1)
        
        # MP Bar (Blue)
        cv2.rectangle(frame, (p1_x, p1_y + 30), (p1_x + 150, p1_y + 42), (50, 0, 0), -1)
        mp1_w = int((self.player1.mana / 100) * 150)
        cv2.rectangle(frame, (p1_x, p1_y + 30), (p1_x + mp1_w, p1_y + 42), (255, 150, 50), -1)
        cv2.rectangle(frame, (p1_x, p1_y + 30), (p1_x + 150, p1_y + 42), (255, 200, 100), 1)

        # 3. Draw Player 2 UI (Top Right)
        p2_x = w - 240
        p2_y = 30
        
        # HP Bar
        cv2.rectangle(frame, (p2_x, p2_y + 10), (p2_x + 150, p2_y + 22), (0, 0, 50), -1)
        hp2_w = int((self.player2.health / 100) * 150)
        cv2.rectangle(frame, (p2_x + 150 - hp2_w, p2_y + 10), (p2_x + 150, p2_y + 22), (50, 50, 200), -1)
        cv2.rectangle(frame, (p2_x, p2_y + 10), (p2_x + 150, p2_y + 22), (100, 100, 255), 1)
        
        # MP Bar
        cv2.rectangle(frame, (p2_x, p2_y + 30), (p2_x + 150, p2_y + 42), (50, 0, 0), -1)
        mp2_w = int((self.player2.mana / 100) * 150)
        cv2.rectangle(frame, (p2_x + 150 - mp2_w, p2_y + 30), (p2_x + 150, p2_y + 42), (255, 150, 50), -1)
        cv2.rectangle(frame, (p2_x, p2_y + 30), (p2_x + 150, p2_y + 42), (255, 200, 100), 1)

        return frame

    def draw_ui_text(self, draw, pil_img, w, h):
        cx = w // 2
        gold = (255, 200, 50) # RGB in PIL
        
        # Title
        text = "ARCANA"
        bbox = draw.textbbox((0, 0), text, font=self.font_title)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw//2 + 2, 22), text, font=self.font_title, fill=(0,0,0))
        draw.text((cx - tw//2, 20), text, font=self.font_title, fill=gold)
        
        subtitle = "WIZARD DUEL"
        bbox2 = draw.textbbox((0, 0), subtitle, font=self.font_small)
        stw = bbox2[2] - bbox2[0]
        draw.text((cx - stw//2, 60), subtitle, font=self.font_small, fill=(200, 200, 200))
        
        # P1 Labels
        p1_x = 20
        p1_y = 30
        draw.text((p1_x, p1_y - 25), "Player 1", font=self.font_ui, fill=(255, 255, 255))
        draw.text((p1_x + 160, p1_y + 5), f"HP: {int(self.player1.health)}", font=self.font_small, fill=(255, 200, 200))
        draw.text((p1_x + 160, p1_y + 25), f"Mana: {int(self.player1.mana)}", font=self.font_small, fill=(200, 200, 255))
        
        # P2 Labels
        p2_x = w - 240
        p2_y = 30
        
        p2_text = "Player 2"
        bbox3 = draw.textbbox((0, 0), p2_text, font=self.font_ui)
        p2_tw = bbox3[2] - bbox3[0]
        draw.text((p2_x + 150 - p2_tw, p2_y - 25), p2_text, font=self.font_ui, fill=(255, 255, 255))
        
        hp2_text = f"HP: {int(self.player2.health)}"
        bbox4 = draw.textbbox((0, 0), hp2_text, font=self.font_small)
        draw.text((p2_x - (bbox4[2]-bbox4[0]) - 10, p2_y + 5), hp2_text, font=self.font_small, fill=(255, 200, 200))
        
        mp2_text = f"Mana: {int(self.player2.mana)}"
        bbox5 = draw.textbbox((0, 0), mp2_text, font=self.font_small)
        draw.text((p2_x - (bbox5[2]-bbox5[0]) - 10, p2_y + 25), mp2_text, font=self.font_small, fill=(200, 200, 255))

    def draw_spell_panel(self, pil_img, draw, x, y, player):
        width = 250
        height = 80
        
        if player.spell_state in ["CHARGING", "CAST"] and player.locked_spell:
            spell_name = player.locked_spell.name
            gesture = f"({player.locked_gesture})"
            b, g, r = self.get_spell_color(spell_name, (255,255,255))
            color = (r, g, b)
        else:
            return 
            
        # Draw Parchment Texture
        if self.parchment_img:
            pil_img.paste(self.parchment_img, (x, y), self.parchment_img)
        else:
            draw.rectangle([x, y, x+width, y+height], fill=(20, 10, 5, 200))
            draw.rectangle([x, y, x+width, y+height], outline=color, width=2)
            
        # Text
        draw.text((x + 70, y + 20), f"{spell_name} Spell", font=self.font_ui, fill=color)
        draw.text((x + 70, y + 45), gesture, font=self.font_small, fill=(80, 40, 20))
        
        # Icon Proxy
        draw.ellipse([x + 20, y + 25, x + 50, y + 55], outline=color, width=2)

    def run(self):
        if not self.camera.open_camera():
            return

        width, height = self.camera.get_dimensions()
        print(f"Camera Resolution : {width} x {height}")
        
        self.ambient = AmbientParticles(100, width, height)

        while True:
            current_time = time.time()
            delta_time = current_time - self.prev_time
            self.prev_time = current_time

            if not self.game_over:
                MANA_REGEN_RATE = 5.0
                self.player1.restore_mana(MANA_REGEN_RATE * delta_time)
                self.player2.restore_mana(MANA_REGEN_RATE * delta_time)

            frame = self.camera.get_frame()

            if frame is None:
                break

            frame = cv2.flip(frame, 1)
            
            p1_color = self.get_spell_color(self.player1.locked_spell.name if self.player1.locked_spell else None, (150, 200, 255))
            p2_color = self.get_spell_color(self.player2.locked_spell.name if self.player2.locked_spell else None, (150, 200, 255))
            
            # Draw ambient particles early so they stay in background
            frame = self.ambient.draw(frame, current_time, p1_color, p2_color)
            
            timestamp = int(time.time()*1000)
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

            if not self.game_over:
                self.p1_prev_state = self.player1.spell_state
                self.p2_prev_state = self.player2.spell_state
                
                self.player1.update_spell_state(delta_time, p1_gesture, self.player2, self.spell_manager)
                self.player2.update_spell_state(delta_time, p2_gesture, self.player1, self.spell_manager)

                # Update Projectiles
                for proj in self.projectiles:
                    proj['obj'].update(delta_time)
                    if proj['obj'].reached_target:
                        target_player = proj['target_player']
                        
                        # Check for Shield Reflection
                        if target_player.spell_state == "CAST" and target_player.locked_spell and target_player.locked_spell.name == "Shield":
                            # Reflect back!
                            p = proj['obj']
                            
                            # Switch target player
                            other_player = self.player2 if target_player == self.player1 else self.player1
                            proj['target_player'] = other_player
                            
                            # Determine new target coordinates
                            if other_player.hand_landmarks:
                                new_tx = other_player.hand_landmarks[0].x * self.camera.get_dimensions()[0]
                                new_ty = other_player.hand_landmarks[0].y * self.camera.get_dimensions()[1]
                            else:
                                # Fallback positions
                                new_tx = self.camera.get_dimensions()[0] * (0.8 if other_player == self.player2 else 0.2)
                                new_ty = self.camera.get_dimensions()[1] * 0.5
                                
                            # Update projectile trajectory
                            p.target_x = new_tx
                            p.target_y = new_ty
                            dx = p.target_x - p.x
                            dy = p.target_y - p.y
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                p.vx = (dx / dist) * p.speed
                                p.vy = (dy / dist) * p.speed
                            
                            p.reached_target = False
                            p.active = True
                            
                            # Add a UI message to the shielder
                            target_player.ui_message = "REFLECTED!"
                        else:
                            # Normal hit
                            target_player.take_damage(proj['damage'])
                            proj['obj'].active = False
                        
                self.projectiles = [p for p in self.projectiles if p['obj'].active]

                # Check for Cast Transitions
                if self.player1.spell_state == "CAST" and self.p1_prev_state == "CHARGING" and self.player1.locked_spell:
                    if self.player1.locked_spell.name != "Shield": # Prevent Shield from traveling
                        if self.player1.hand_landmarks:
                            wrist1 = self.player1.hand_landmarks[0]
                            target_pos = (0.8, 0.5)
                            if self.player2.hand_landmarks:
                                target_pos = (self.player2.hand_landmarks[0].x, self.player2.hand_landmarks[0].y)
                            
                            proj = SpellProjectile(
                                wrist1.x * width, wrist1.y * height, 
                                target_pos[0] * width, target_pos[1] * height, 
                                duration=0.6
                            )
                            self.projectiles.append({
                                'obj': proj,
                                'spell_name': self.player1.locked_spell.name,
                                'target_player': self.player2,
                                'damage': self.player1.last_cast_damage
                            })

                if self.player2.spell_state == "CAST" and self.p2_prev_state == "CHARGING" and self.player2.locked_spell:
                    if self.player2.locked_spell.name != "Shield":
                        if self.player2.hand_landmarks:
                            wrist2 = self.player2.hand_landmarks[0]
                            target_pos = (0.2, 0.5)
                            if self.player1.hand_landmarks:
                                target_pos = (self.player1.hand_landmarks[0].x, self.player1.hand_landmarks[0].y)
                                
                            proj = SpellProjectile(
                                wrist2.x * width, wrist2.y * height, 
                                target_pos[0] * width, target_pos[1] * height, 
                                duration=0.6
                            )
                            self.projectiles.append({
                                'obj': proj,
                                'spell_name': self.player2.locked_spell.name,
                                'target_player': self.player1,
                                'damage': self.player2.last_cast_damage
                            })

            # ---------------- DRAW ---------------- #
            
            if not self.game_over:
                # 1. Draw Charging Auras (or Shield while CAST)
                for player in [self.player1, self.player2]:
                    if (player.spell_state == "CHARGING" or (player.spell_state == "CAST" and player.locked_spell and player.locked_spell.name == "Shield")) and player.locked_spell:
                        spell_name = player.locked_spell.name
                        charge_amount = player.charge_time if player.spell_state == "CHARGING" else 5.0
                        if spell_name == "Fireball":
                            frame = self.fire_vfx.draw_charging(frame, player.hand_landmarks, charge_amount)
                        elif spell_name == "Ice Blast":
                            frame = self.ice_vfx.draw_charging(frame, player.hand_landmarks, charge_amount)
                        elif spell_name == "Lightning":
                            frame = self.lightning_vfx.draw_charging(frame, player.hand_landmarks, charge_amount)
                        elif spell_name == "Wind Slash":
                            frame = self.wind_vfx.draw_charging(frame, player.hand_landmarks, charge_amount)
                        elif spell_name == "Shield":
                            frame = self.shield_vfx.draw_charging(frame, player.hand_landmarks, charge_amount)
                            
                # 2. Draw Traveling Projectiles
                for proj in self.projectiles:
                    p = proj['obj']
                    s_name = proj['spell_name']
                    if s_name == "Fireball":
                        frame = self.fire_vfx.draw_projectile(frame, p.x, p.y)
                    elif s_name == "Ice Blast":
                        frame = self.ice_vfx.draw_projectile(frame, p.x, p.y)
                    elif s_name == "Lightning":
                        frame = self.lightning_vfx.draw_projectile(frame, p.x, p.y)
                    elif s_name == "Wind Slash":
                        frame = self.wind_vfx.draw_projectile(frame, p.x, p.y)

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
                    
            # ---------------- UI (OpenCV Layer) ---------------- #
            # We draw HP/MP bars and dividers via OpenCV before PIL
            frame = self.draw_ui_base(frame, width, height)
            
            # ---------------- UI (PIL Layer) ---------------- #
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(pil_img)
            
            self.draw_ui_text(draw, pil_img, width, height)
            
            # Spell Panels
            self.draw_spell_panel(pil_img, draw, 30, height - 100, self.player1)
            self.draw_spell_panel(pil_img, draw, width - 280, height - 100, self.player2)
            
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            if self.game_over:
                text = f"{self.winner} WINS!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 2, 5)[0]
                text_x = (width - text_size[0]) // 2
                text_y = height // 2
                cv2.rectangle(frame, (text_x - 20, text_y - text_size[1] - 20), 
                              (text_x + text_size[0] + 20, text_y + 20), (0, 0, 0), -1)
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 215, 255), 5)
                
                if time.time() - self.game_over_time > 4.0:
                    break
                    
            fps = 1 / delta_time if delta_time > 0 else 0
            cv2.putText(frame, f"FPS: {int(fps)}", (10, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.camera.release_camera()