import cv2
import time
import numpy as np
import random
import math
import os
import pygame
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
        # Initialize audio mixer
        pygame.mixer.init()
        if os.path.exists("assets/background_music.mp3"):
            pygame.mixer.music.load("assets/background_music.mp3")
            pygame.mixer.music.set_volume(0.25)  # slightly lighter background music
            pygame.mixer.music.play(-1, fade_ms=2000)  # loop indefinitely with 2s fade in
            
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
        
        # Spell Audio Setup
        self.spell_sounds = {}
        sound_files = {
            "Wind Slash": "assets/wind.wav",
            "Fireball": "assets/fireball.mp3",
            "Lightning": "assets/lighting.mp3",  # Fixed spelling to match user's file
            "Ice Blast": "assets/ice.mp3"
        }
        for spell_name, fname in sound_files.items():
            if os.path.exists(fname):
                snd = pygame.mixer.Sound(fname)
                snd.set_volume(1.0)
                self.spell_sounds[spell_name] = snd
                
        self.p1_channel = pygame.mixer.Channel(1)
        self.p2_channel = pygame.mixer.Channel(2)
        self.p1_sound_playing = False
        self.p2_sound_playing = False
        
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
            self.font_huge = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 52)
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 40)
            self.font_ui = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 28)
            self.font_small = ImageFont.truetype("C:/Windows/Fonts/OLDENGL.TTF", 16)
        except:
            self.font_huge = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_ui = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
        try:
            self.top_bg = cv2.imread("assets/magical_bg.jpg")
            self.top_bg_resized = None
        except:
            self.top_bg = None
            
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

    def draw_custom_bar(self, frame, x, y, width, height, point_w, percentage, bg_color, fill_color, border_color, reverse=False):
        bg_pts = np.array([
            [x, y + height//2], [x + point_w, y], [x + width - point_w, y],
            [x + width, y + height//2], [x + width - point_w, y + height], [x + point_w, y + height]
        ], np.int32)
        cv2.fillPoly(frame, [bg_pts], bg_color)
        
        fill_width = int(width * percentage)
        if fill_width > 0:
            fill_pts = []
            if not reverse:
                fill_pts.append([x, y + height//2])
                if fill_width > point_w:
                    fill_pts.append([x + point_w, y])
                    if fill_width > width - point_w:
                        fill_pts.append([x + width - point_w, y])
                        fill_pts.append([x + fill_width, y + height//2])
                        fill_pts.append([x + width - point_w, y + height])
                    else:
                        fill_pts.append([x + fill_width, y])
                        fill_pts.append([x + fill_width, y + height])
                    fill_pts.append([x + point_w, y + height])
                else:
                    y_top = y + height//2 - int((fill_width / point_w) * (height//2))
                    y_bot = y + height//2 + int((fill_width / point_w) * (height//2))
                    fill_pts.append([x + fill_width, y_top])
                    fill_pts.append([x + fill_width, y_bot])
            else:
                fill_pts.append([x + width, y + height//2])
                if fill_width > point_w:
                    fill_pts.append([x + width - point_w, y])
                    if fill_width > width - point_w:
                        fill_pts.append([x + point_w, y])
                        fill_pts.append([x + width - fill_width, y + height//2])
                        fill_pts.append([x + point_w, y + height])
                    else:
                        fill_pts.append([x + width - fill_width, y])
                        fill_pts.append([x + width - fill_width, y + height])
                    fill_pts.append([x + width - point_w, y + height])
                else:
                    y_top = y + height//2 - int((fill_width / point_w) * (height//2))
                    y_bot = y + height//2 + int((fill_width / point_w) * (height//2))
                    fill_pts.append([x + width - fill_width, y_top])
                    fill_pts.append([x + width - fill_width, y_bot])
                
            cv2.fillPoly(frame, [np.array(fill_pts, np.int32)], fill_color)
            
        cv2.polylines(frame, [bg_pts], True, border_color, 2)
        
        d_size = 5
        for cx, cy in [(x, y + height//2), (x + width, y + height//2)]:
            d_pts = np.array([[cx, cy - d_size], [cx + d_size, cy], [cx, cy + d_size], [cx - d_size, cy]], np.int32)
            cv2.fillPoly(frame, [d_pts], border_color)
            cv2.polylines(frame, [d_pts], True, (0, 0, 0), 1)

    def draw_ui_base(self, frame, w, h):
        banner_h = 150
        if hasattr(self, 'top_bg') and self.top_bg is not None:
            if self.top_bg_resized is None or self.top_bg_resized.shape[1] != w:
                bg_w = w
                bg_h = int(w * self.top_bg.shape[0] / self.top_bg.shape[1])
                bg_resized = cv2.resize(self.top_bg, (bg_w, bg_h))
                y_start = bg_h // 2 - banner_h // 2
                if y_start < 0: y_start = 0
                cropped = bg_resized[y_start:y_start+banner_h, 0:w]
                if cropped.shape[0] != banner_h:
                    cropped = cv2.resize(cropped, (w, banner_h))
                self.top_bg_resized = cropped
            frame[0:banner_h, 0:w] = self.top_bg_resized
            
        bar_w = 230
        bar_h = 16
        point_w = 12
        
        gold = (50, 170, 255) # BGR
        bg_color = (20, 20, 20)
        gold_dark = (20, 100, 150) # BGR
        gold_light = (150, 220, 255) # BGR

        self.draw_divider(frame, 0, banner_h, w, 6, gold)
        
        # Vertical divider
        cv2.line(frame, (w // 2, banner_h), (w // 2, h), gold, 2)
        
        p1_x = 20
        p1_y = 100
        self.draw_custom_bar(frame, p1_x, p1_y, bar_w, bar_h, point_w, self.player1.health/100.0, bg_color, (30, 30, 220), gold, reverse=False)
        self.draw_custom_bar(frame, p1_x, p1_y + 25, bar_w, bar_h, point_w, self.player1.mana/100.0, bg_color, (255, 120, 20), gold, reverse=False)
        
        p2_x = w - bar_w - 20
        p2_y = 100
        self.draw_custom_bar(frame, p2_x, p2_y, bar_w, bar_h, point_w, self.player2.health/100.0, bg_color, (30, 30, 220), gold, reverse=True)
        self.draw_custom_bar(frame, p2_x, p2_y + 25, bar_w, bar_h, point_w, self.player2.mana/100.0, bg_color, (255, 120, 20), gold, reverse=True)

        return frame

    def draw_ui_text(self, draw, pil_img, w, h):
        cx = w // 2
        gold = (255, 200, 50) # RGB in PIL
        
        text = "ARCANA"
        bbox = draw.textbbox((0, 0), text, font=self.font_huge)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw//2 + 3, 13), text, font=self.font_huge, fill=(0,0,0))
        draw.text((cx - tw//2, 10), text, font=self.font_huge, fill=gold)
        
        subtitle = "<>- WIZARD DUEL -<>"
        bbox2 = draw.textbbox((0, 0), subtitle, font=self.font_small)
        stw = bbox2[2] - bbox2[0]
        draw.text((cx - stw//2, 75), subtitle, font=self.font_small, fill=(0, 0, 0))
        
        p1_x = 20
        p1_y = 100
        draw.text((p1_x + 10, p1_y - 35), "Player 1", font=self.font_ui, fill=(255, 255, 255))
        
        p2_x = w - 250
        p2_y = 100
        p2_text = "Player 2"
        bbox3 = draw.textbbox((0, 0), p2_text, font=self.font_ui)
        p2_tw = bbox3[2] - bbox3[0]
        draw.text((p2_x + 230 - p2_tw - 10, p2_y - 35), p2_text, font=self.font_ui, fill=(255, 255, 255))

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
        draw.text((x + 20, y + 15), f"{spell_name} Spell", font=self.font_ui, fill=color)
        # Made the sub-text brighter so it's visible on the brown background
        draw.text((x + 20, y + 45), gesture, font=self.font_small, fill=(240, 220, 190))

    def draw_divider(self, frame, x, y, width, thickness, color):
        # Draw main horizontal line
        cv2.rectangle(frame, (x, y - thickness//2), (x + width, y + thickness//2), color, -1)
        
        # Draw decorative diamonds
        d_size = thickness + 2
        for cx in [x + 20, x + width // 2, x + width - 20]:
            pts = np.array([
                [cx, y - d_size],
                [cx + d_size, y],
                [cx, y + d_size],
                [cx - d_size, y]
            ], np.int32)
            cv2.fillPoly(frame, [pts], color)
            cv2.polylines(frame, [pts], True, (0, 0, 0), 1)

    def update_spell_audio(self, player, prev_state, channel, is_p1):
        if not player.locked_spell:
            if channel.get_busy():
                channel.fadeout(500)
            if is_p1: self.p1_sound_playing = False
            else: self.p2_sound_playing = False
            return
            
        sound = self.spell_sounds.get(player.locked_spell.name)
        if not sound:
            return
            
        if player.spell_state == "CHARGING":
            is_playing = self.p1_sound_playing if is_p1 else self.p2_sound_playing
            if not is_playing:
                channel.play(sound, loops=-1)
                if is_p1: self.p1_sound_playing = True
                else: self.p2_sound_playing = True
                
            # Start louder and reach 100% volume in half the time
            vol = min(1.0, 0.5 + (player.charge_time / 2.5) * 0.5)
            channel.set_volume(vol)
            
        elif player.spell_state == "CAST" and prev_state == "CHARGING":
            channel.fadeout(1500)
            if is_p1: self.p1_sound_playing = False
            else: self.p2_sound_playing = False
            
        elif player.spell_state == "IDLE" and prev_state == "CHARGING":
            if channel.get_busy():
                channel.fadeout(500)
            if is_p1: self.p1_sound_playing = False
            else: self.p2_sound_playing = False

    def draw_winner_panel(self, draw, w, h, text):
        panel_w = 460
        panel_h = 100
        cx = w // 2
        cy = h // 2
        x1 = cx - panel_w // 2
        y1 = cy - panel_h // 2
        x2 = cx + panel_w // 2
        y2 = cy + panel_h // 2
        
        bg_color = (15, 10, 5, 240)
        gold = (255, 180, 50)
        gold_light = (255, 230, 150)
        gold_dark = (120, 70, 20)
        
        draw.rectangle([x1, y1, x2, y2], fill=bg_color, outline=gold, width=4)
        draw.rectangle([x1+6, y1+6, x2-6, y2-6], outline=gold_dark, width=2)
        
        d_size = 10
        for dx, dy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            d_pts = [(dx, dy - d_size), (dx + d_size, dy), (dx, dy + d_size), (dx - d_size, dy)]
            draw.polygon(d_pts, fill=gold, outline=(0,0,0))
            
        d_size_l = 15
        for dx, dy in [(cx, y1), (cx, y2), (x1, cy), (x2, cy)]:
            d_pts = [(dx, dy - d_size_l), (dx + d_size_l, dy), (dx, dy + d_size_l), (dx - d_size_l, dy)]
            draw.polygon(d_pts, fill=gold_light, outline=(0,0,0))
            
        bbox = draw.textbbox((0, 0), text, font=self.font_huge)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        
        draw.text((cx - tw//2 + 3, cy - th//2 - 10), text, font=self.font_huge, fill=(0,0,0))
        draw.text((cx - tw//2, cy - th//2 - 13), text, font=self.font_huge, fill=gold)

    def run(self):
        if not self.camera.open_camera():
            return

        width, height = self.camera.get_dimensions()
        print(f"Camera Resolution : {width} x {height}")
        
        start_screen_path = "assets/start_screen.png"
        if os.path.exists(start_screen_path):
            start_img = cv2.imread(start_screen_path)
            if start_img is not None:
                start_img = cv2.resize(start_img, (width, height))
                cv2.imshow("ARCANA", start_img)
                cv2.waitKey(100) # Force render
                print("Start screen loaded. Press 's' to start or 'q' to quit.")
                while True:
                    key = cv2.waitKey(10) & 0xFF
                    if key == ord('s') or key == ord('S'):
                        if os.path.exists("assets/click.wav"):
                            click_sound = pygame.mixer.Sound("assets/click.wav")
                            click_sound.set_volume(1.0)
                            click_sound.play()
                        break
                    elif key == ord('q') or key == ord('Q'):
                        pygame.mixer.music.stop()
                        self.camera.release_camera()
                        return
        
        self.ambient = AmbientParticles(100, width, height)

        while True:
            current_time = time.time()
            delta_time = current_time - self.prev_time
            self.prev_time = current_time

            if not self.game_over:
                MANA_REGEN_RATE = 8.0
                SHIELD_DRAIN_RATE = 5.0
                for p in (self.player1, self.player2):
                    if p.spell_state in ["CHARGING", "CAST"] and p.locked_spell and p.locked_spell.name == "Shield":
                        p.mana -= SHIELD_DRAIN_RATE * delta_time
                        if p.mana <= 0:
                            p.mana = 0
                            if p.spell_state != "IDLE":
                                p.spell_state = "CANCELLED"
                                p.ui_message = "SHIELD BROKEN (NO MANA)!"
                                p.message_timer = 1.5
                    else:
                        p.restore_mana(MANA_REGEN_RATE * delta_time)

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

                self.update_spell_audio(self.player1, self.p1_prev_state, self.p1_channel, True)
                self.update_spell_audio(self.player2, self.p2_prev_state, self.p2_channel, False)

                # Update Projectiles
                for proj in self.projectiles:
                    proj['obj'].update(delta_time)
                    if proj['obj'].reached_target:
                        target_player = proj['target_player']
                        
                        # Check for Shield Block
                        if target_player.spell_state in ["CHARGING", "CAST"] and target_player.locked_spell and target_player.locked_spell.name == "Shield":
                            # Block the projectile
                            proj['obj'].active = False
                            
                            # Add a UI message to the shielder
                            target_player.ui_message = "BLOCKED!"
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
                    pygame.mixer.music.fadeout(4000)
                elif self.player2.is_defeated:
                    self.game_over = True
                    self.winner = "PLAYER 1"
                    self.game_over_time = time.time()
                    pygame.mixer.music.fadeout(4000)
                    
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
            
            if self.game_over:
                end_screen_path = "assets/end_player1.png" if self.winner == "PLAYER 1" else "assets/end_player2.png"
                end_img = None
                if os.path.exists(end_screen_path):
                    end_img = cv2.imread(end_screen_path)
                
                if end_img is not None:
                    end_img = cv2.resize(end_img, (width, height))
                    # Overwrite the PIL image so it gets drawn to the final frame
                    pil_img = Image.fromarray(cv2.cvtColor(end_img, cv2.COLOR_BGR2RGB))
                else:
                    text = f"{self.winner} WINS!"
                    self.draw_winner_panel(draw, width, height, text)
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            if self.game_over:
                if time.time() - self.game_over_time > 4.0:
                    break
                    
            fps = 1 / delta_time if delta_time > 0 else 0
            cv2.putText(frame, f"FPS: {int(fps)}", (10, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("ARCANA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.camera.release_camera()