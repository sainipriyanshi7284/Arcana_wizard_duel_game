import cv2
import numpy as np
import random
import math
import time

class LightningVFX:
    def __init__(self):
        self.sparks = []

    def add_spark(self, x, y):
        self.sparks.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-10, 10),
            'vy': random.uniform(-10, 10),
            'life': 1.0,
            'decay': random.uniform(0.1, 0.2)
        })

    def draw_lightning_bolt(self, frame, x1, y1, x2, y2, color, thickness, segments=5, displacement=20):
        # Draw a jagged line between two points
        pts = [(x1, y1)]
        for i in range(1, segments):
            t = i / segments
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            cx += random.randint(-displacement, displacement)
            cy += random.randint(-displacement, displacement)
            pts.append((int(cx), int(cy)))
        pts.append((x2, y2))
        
        for i in range(len(pts) - 1):
            cv2.line(frame, pts[i], pts[i+1], color, thickness)

    def draw_charging(self, frame, hand_landmarks, charge_time):
        if not hand_landmarks:
            return frame

        h, w, _ = frame.shape
        wrist = hand_landmarks[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        
        # Pointing_Up -> Index finger tip is landmark 8
        tip = hand_landmarks[8]
        tx, ty = int(tip.x * w), int(tip.y * h)

        overlay = np.zeros_like(frame)
        
        # 1. Base glow at the fingertip
        glow_radius = int(50 + charge_time * 20)
        cv2.circle(overlay, (tx, ty), glow_radius, (200, 50, 200), -1)
        cv2.circle(overlay, (tx, ty), int(glow_radius*0.5), (255, 100, 255), -1)
        
        # 2. Electric Arcs around the hand
        if random.random() < 0.8:
            for _ in range(2):
                idx1 = random.choice([0, 4, 12, 16, 20])
                p1 = hand_landmarks[idx1]
                p1x, p1y = int(p1.x * w), int(p1.y * h)
                self.draw_lightning_bolt(overlay, p1x, p1y, tx, ty, (255, 150, 255), 2, segments=4, displacement=15)
                self.draw_lightning_bolt(overlay, p1x, p1y, tx, ty, (255, 255, 255), 1, segments=4, displacement=15)
        
        # 3. Random branching lightning from fingertip
        if random.random() < 0.6:
            for _ in range(2):
                angle = random.uniform(0, 2*math.pi)
                length = random.randint(50, 150)
                ex, ey = int(tx + math.cos(angle)*length), int(ty + math.sin(angle)*length)
                self.draw_lightning_bolt(overlay, tx, ty, ex, ey, (255, 100, 255), 2, segments=5, displacement=20)
                if random.random() < 0.5:
                    self.add_spark(ex, ey)
                    
        cv2.GaussianBlur(overlay, (15, 15), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        # Draw some sharp lightning directly on frame
        if random.random() < 0.5:
            angle = random.uniform(0, 2*math.pi)
            length = random.randint(60, 180)
            ex, ey = int(tx + math.cos(angle)*length), int(ty + math.sin(angle)*length)
            self.draw_lightning_bolt(frame, tx, ty, ex, ey, (255, 255, 255), 2, segments=5, displacement=25)

        self._update_and_draw_sparks(frame)
        return frame

    def draw_projectile(self, frame, x, y):
        overlay = np.zeros_like(frame)
        
        # Core electric ball
        cv2.circle(overlay, (int(x), int(y)), 40, (200, 50, 200), -1)
        
        # Jagged trailing lightning
        self.draw_lightning_bolt(overlay, int(x), int(y), int(x - random.randint(30, 80)), int(y + random.randint(-40, 40)), (255, 150, 255), 3, segments=4)
        self.draw_lightning_bolt(overlay, int(x), int(y), int(x - random.randint(30, 80)), int(y + random.randint(-40, 40)), (255, 255, 255), 1, segments=4)
        
        cv2.GaussianBlur(overlay, (21, 21), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        cv2.circle(frame, (int(x), int(y)), 15, (255, 255, 255), -1)
        
        if random.random() < 0.5:
            self.add_spark(x, y)
        self._update_and_draw_sparks(frame)
        
        return frame

    def _update_and_draw_sparks(self, frame):
        overlay = np.zeros_like(frame)
        for s in self.sparks:
            s['x'] += s['vx']
            s['y'] += s['vy']
            s['life'] -= s['decay']
            if s['life'] > 0:
                cv2.circle(overlay, (int(s['x']), int(s['y'])), int(4 * s['life']), (255, 150, 255), -1)
                
        cv2.GaussianBlur(overlay, (7, 7), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        self.sparks = [s for s in self.sparks if s['life'] > 0]
