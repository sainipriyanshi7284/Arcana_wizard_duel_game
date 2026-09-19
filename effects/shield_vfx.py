import cv2
import numpy as np
import math
import time
import random

class ShieldVFX:
    def __init__(self):
        pass

    def draw_diamond(self, frame, x, y, size, color, thickness=1):
        pts = np.array([
            [x, y - size],
            [x + size, y],
            [x, y + size],
            [x - size, y]
        ], np.int32)
        if thickness < 0:
            cv2.fillPoly(frame, [pts], color)
        else:
            cv2.polylines(frame, [pts], True, color, thickness)

    def draw_charging(self, frame, hand_landmarks, charge_time):
        if not hand_landmarks:
            return frame
            
        h, w, _ = frame.shape
        wrist = hand_landmarks[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        
        t = time.time()
        
        overlay = np.zeros_like(frame)
        
        base_radius = int(120 + charge_time * 20)
        color = (150, 200, 255) # light golden/yellow/white
        glow_color = (50, 150, 255)
        
        # 1. Inner Circle
        r1 = int(base_radius * 0.6)
        cv2.circle(overlay, (wx, wy), r1, (30, 80, 120), 2)
        
        # 2. Main Middle Circle
        r2 = base_radius
        cv2.circle(overlay, (wx, wy), r2, (50, 100, 150), 2)
        
        # 3. Outer Circle with segments
        r3 = int(base_radius * 1.3)
        for i in range(12):
            start_angle = (i / 12.0) * 360 + (t * 20)
            end_angle = start_angle + 20
            cv2.ellipse(overlay, (wx, wy), (r3, r3), 0, start_angle, end_angle, (40, 90, 140), 2)
            
        # 4. Diamonds on the middle ring
        for i in range(8):
            Q = (i / 8.0) * 2 * math.pi + (t * 0.5)
            px = wx + int(math.cos(Q) * r2)
            py = wy + int(math.sin(Q) * r2)
            self.draw_diamond(overlay, px, py, 6, (100, 200, 255), -1)
            
        # 5. Glowing Orbs/Clusters on the rings
        # Group of 3 glowing orbs on outer ring
        Q_group = (t * 1.5)
        for offset in [-0.1, 0, 0.1]:
            Q_orb = Q_group + offset
            px = wx + int(math.cos(Q_orb) * r3)
            py = wy + int(math.sin(Q_orb) * r3)
            cv2.circle(overlay, (px, py), 8, glow_color, -1)
            cv2.circle(overlay, (px, py), 4, (200, 255, 255), -1)
            
        # Single glowing orbs on inner ring
        for i in range(3):
            Q_orb = (i / 3.0) * 2 * math.pi - (t * 2.0)
            px = wx + int(math.cos(Q_orb) * r1)
            py = wy + int(math.sin(Q_orb) * r1)
            cv2.circle(overlay, (px, py), 6, glow_color, -1)
            cv2.circle(overlay, (px, py), 3, (200, 255, 255), -1)

        # Apply a slight blur to the overlay to create glow
        blurred_overlay = cv2.GaussianBlur(overlay, (15, 15), 0)
        
        # Additive blending to prevent background dimming
        cv2.add(frame, blurred_overlay, dst=frame)
        cv2.add(frame, overlay, dst=frame) # Add sharp lines on top
            
        return frame

    def draw_projectile(self, frame, x, y):
        # Shield does not travel as a projectile
        return frame
