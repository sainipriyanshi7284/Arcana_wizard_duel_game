import cv2
import numpy as np
import random
import math
import time

class WindVFX:
    def __init__(self):
        self.dust = []

    def add_dust(self, x, y):
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(2, 6)
        self.dust.append({
            'x': x,
            'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': 1.0,
            'decay': random.uniform(0.02, 0.05),
            'angle': angle,
            'orbit_radius': random.randint(20, 80)
        })

    def draw_charging(self, frame, hand_landmarks, charge_time):
        if not hand_landmarks:
            return frame

        h, w, _ = frame.shape
        wrist = hand_landmarks[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        
        # Thumb up -> Thumb tip is landmark 4
        tip = hand_landmarks[4]
        tx, ty = int(tip.x * w), int(tip.y * h)

        overlay = np.zeros_like(frame)
        t = time.time()
        
        # Base swirling winds
        radius = int(60 + charge_time * 20)
        
        for i in range(3):
            angle_offset = t * (5 + i*2)
            # Create elliptical swirling rings
            axes = (radius, int(radius * 0.4))
            angle = (i * 60) + (t * 50)
            
            # Use cv2.ellipse to draw wind arcs
            cv2.ellipse(overlay, (tx, ty), axes, angle, 0, 180, (200, 255, 200), 2)
            cv2.ellipse(overlay, (tx, ty), axes, angle, 180, 270, (255, 255, 255), 4)
            
        # Draw some fast trailing wind lines
        if random.random() < 0.7:
            for _ in range(2):
                start_a = random.uniform(0, 360)
                end_a = start_a + random.uniform(45, 90)
                cv2.ellipse(overlay, (tx, ty), (radius+20, radius+20), t*100, start_a, end_a, (150, 255, 200), 3)

        cv2.GaussianBlur(overlay, (15, 15), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        # Core glowing orb
        cv2.circle(frame, (tx, ty), 15, (200, 255, 200), -1)
        cv2.circle(frame, (tx, ty), 8, (255, 255, 255), -1)
        
        if random.random() < 0.6:
            self.add_dust(tx, ty)
            
        self._update_and_draw_dust(frame, tx, ty, t)

        return frame

    def draw_projectile(self, frame, x, y):
        overlay = np.zeros_like(frame)
        t = time.time()
        
        # Wind crescent / Tornado core
        axes = (40, 20)
        angle = t * 300
        
        cv2.ellipse(overlay, (int(x), int(y)), axes, angle, 0, 270, (255, 255, 255), 6)
        cv2.ellipse(overlay, (int(x), int(y)), (30, 30), -angle, 0, 180, (150, 255, 200), 4)
        
        cv2.GaussianBlur(overlay, (15, 15), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        # Core
        cv2.circle(frame, (int(x), int(y)), 10, (255, 255, 255), -1)
        
        self.add_dust(x + random.randint(-20, 20), y + random.randint(-20, 20))
        self._update_and_draw_dust(frame, x, y, t)
        
        return frame

    def _update_and_draw_dust(self, frame, cx, cy, t):
        overlay = np.zeros_like(frame)
        for d in self.dust:
            # Add some orbital mechanics
            d['angle'] += 0.2
            d['x'] += d['vx'] + math.cos(d['angle']) * 3
            d['y'] += d['vy'] + math.sin(d['angle']) * 3
            d['life'] -= d['decay']
            
            if d['life'] > 0:
                cv2.circle(overlay, (int(d['x']), int(d['y'])), int(3 * d['life']), (200, 255, 200), -1)
                
        cv2.GaussianBlur(overlay, (9, 9), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        self.dust = [d for d in self.dust if d['life'] > 0]
