import cv2
import numpy as np
import random
import math
import time

class FireVFX:
    def __init__(self):
        self.embers = []
        
    def add_ember(self, x, y):
        self.embers.append({
            'x': x,
            'y': y,
            'speed': random.uniform(3, 8),
            'size': random.randint(2, 6),
            'life': 1.0,
            'angle': random.uniform(0, 2*math.pi)
        })

    def draw_charging(self, frame, hand_landmarks, charge_time):
        """Draws the Fire charging VFX on the hand"""
        if not hand_landmarks:
            return frame

        h, w, _ = frame.shape
        wrist = hand_landmarks[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        
        overlay = np.zeros_like(frame)
        
        # 1. Ambient Radial Glow (Massive)
        glow_radius = int(120 + min(charge_time, 5.0) * 30)
        cv2.circle(overlay, (wx, wy - 50), glow_radius, (0, 80, 200), -1)
        
        # 2. Blurred Flame Puffs (Massive)
        for _ in range(6):
            puff_x = wx + random.randint(-100, 100)
            puff_y = wy - random.randint(50, 150)
            cv2.circle(overlay, (puff_x, puff_y), random.randint(60, 120), (0, 140, 255), -1)

        cv2.GaussianBlur(overlay, (81, 81), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)

        # 3. Flame Polygons (Massive Bonfire Shape)
        outer_pts = []
        num_points = 12
        for i in range(num_points):
            angle = (i / float(num_points)) * 2 * math.pi + (time.time() * 2)
            r = random.randint(glow_radius - 20, glow_radius + 60)
            px = wx + int(math.cos(angle) * r * 0.9) # Slightly wider horizontally
            
            # If pointing upwards (sin < 0), stretch it up into spikes
            if math.sin(angle) < 0:
                py = wy + int(math.sin(angle) * r * 1.8) - random.randint(40, 100)
            else:
                py = wy + int(math.sin(angle) * r * 0.5) # Flatter bottom
                
            outer_pts.append([px, py])
            
        inner_pts = []
        for i in range(num_points):
            angle = (i / float(num_points)) * 2 * math.pi - (time.time() * 3)
            r = random.randint(int(glow_radius*0.4), int(glow_radius*0.7))
            px = wx + int(math.cos(angle) * r * 0.8)
            
            if math.sin(angle) < 0:
                py = wy + int(math.sin(angle) * r * 1.6) - random.randint(20, 60)
            else:
                py = wy + int(math.sin(angle) * r * 0.4)
                
            inner_pts.append([px, py])
        
        poly_overlay = np.zeros_like(frame)
        cv2.fillPoly(poly_overlay, [np.array(outer_pts)], (0, 100, 255)) # Orange
        cv2.fillPoly(poly_overlay, [np.array(inner_pts)], (0, 220, 255)) # Yellow
        cv2.GaussianBlur(poly_overlay, (31, 31), 0, dst=poly_overlay)
        cv2.addWeighted(poly_overlay, 0.7, frame, 1.0, 0, frame) 
        
        # 4. Fingertip Plasma Tendrils
        for tip_idx in [4, 8, 12, 16, 20]:
            tip = hand_landmarks[tip_idx]
            tx, ty = int(tip.x * w), int(tip.y * h)
            
            cx, cy = wx, wy
            for _ in range(3):
                nx = cx + (tx - cx) // 3 + random.randint(-15, 15)
                ny = cy + (ty - cy) // 3 + random.randint(-15, 15)
                cv2.line(frame, (cx, cy), (nx, ny), (100, 200, 255), 2)
                cx, cy = nx, ny
            cv2.line(frame, (cx, cy), (tx, ty), (100, 200, 255), 2)
            
            # Spawn embers from fingertips
            if random.random() < 0.4:
                self.add_ember(tx, ty)
                
        # 5. Rising Ember Particles
        self._update_and_draw_embers(frame)

        return frame

    def draw_projectile(self, frame, x, y):
        # Draw traveling fireball using glow and embers (no solid simple circles)
        overlay = np.zeros_like(frame)
        
        # Core puff
        cv2.circle(overlay, (int(x), int(y)), 30, (0, 100, 255), -1)
        
        # Trailing puff
        cv2.circle(overlay, (int(x - 15), int(y)), 20, (0, 60, 255), -1)
        
        cv2.GaussianBlur(overlay, (41, 41), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        # Central bright plasma
        cv2.circle(frame, (int(x), int(y)), 8, (150, 255, 255), -1)
        
        # Spawn trail embers
        for _ in range(2):
            self.add_ember(x + random.randint(-15, 15), y + random.randint(-15, 15))
            
        self._update_and_draw_embers(frame)
        return frame

    def _update_and_draw_embers(self, frame):
        for ember in self.embers:
            ember['y'] -= ember['speed']
            # sin() for sideways movement
            ember['x'] += math.sin(ember['angle']) * 4
            ember['life'] -= 0.04
            ember['angle'] += 0.2
            
            if ember['life'] > 0:
                # Color transitions from yellow to red to dark red
                r, g, b = 255, int(255 * ember['life']), 0
                cv2.circle(frame, (int(ember['x']), int(ember['y'])), int(ember['size'] * ember['life']), (b, g, r), -1)
                
        self.embers = [e for e in self.embers if e['life'] > 0]
