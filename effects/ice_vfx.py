import cv2
import numpy as np
import random
import math

class IceVFX:
    def __init__(self):
        self.snowflakes = []
        self.sparkles = []
        self.mist_particles = []

    def add_snowflake(self, x, y):
        self.snowflakes.append({
            'x': x,
            'y': y,
            'size': random.randint(8, 15),
            'life': 1.0,
            'speed_y': random.uniform(1, 4),
            'speed_x': random.uniform(-1, 1),
            'rotation': random.uniform(0, math.pi),
            'rot_speed': random.uniform(-0.1, 0.1)
        })

    def add_sparkle(self, x, y):
        self.sparkles.append({
            'x': x,
            'y': y,
            'life': 1.0,
            'size': random.randint(5, 12),
            'decay': random.uniform(0.05, 0.1)
        })

    def add_mist(self, x, y):
        self.mist_particles.append({
            'x': x,
            'y': y,
            'life': 1.0,
            'size': random.randint(15, 35),
            'speed_y': random.uniform(-2, 0),
            'speed_x': random.uniform(-2, 2)
        })

    def draw_charging(self, frame, hand_landmarks, charge_time):
        if not hand_landmarks:
            return frame

        h, w, _ = frame.shape
        wrist = hand_landmarks[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)

        # 1. Cyan Mist (Wider spread)
        if random.random() < 0.6:
            self.add_mist(wx + random.randint(-100, 100), wy + random.randint(-100, 100))

        # 2. Crystal spikes along fingers 8 (Index) and 12 (Middle) for Peace gesture
        tip8, mcp8 = hand_landmarks[8], hand_landmarks[5]
        tip12, mcp12 = hand_landmarks[12], hand_landmarks[9]
        
        for tip, mcp in [(tip8, mcp8), (tip12, mcp12)]:
            tx, ty = int(tip.x * w), int(tip.y * h)
            mx, my = int(mcp.x * w), int(mcp.y * h)
            
            # Vector from mcp to tip
            dx, dy = tx - mx, ty - my
            length = math.hypot(dx, dy)
            if length > 0:
                dx, dy = dx / length, dy / length
                
                # Draw crystal spike extending past the tip based on charge (Shorter)
                spike_len = 30 + charge_time * 15
                sx, sy = tx + int(dx * spike_len), ty + int(dy * spike_len)
                
                pts = np.array([
                    [tx - int(dy*20), ty + int(dx*20)],
                    [sx, sy],
                    [tx + int(dy*20), ty - int(dx*20)],
                    [tx - int(dx*30), ty - int(dy*30)]
                ], np.int32)
                
                overlay = np.zeros_like(frame)
                cv2.fillPoly(overlay, [pts], (255, 255, 180))
                cv2.polylines(overlay, [pts], True, (255, 255, 255), 2)
                cv2.addWeighted(overlay, 0.7, frame, 1.0, 0, frame)
                
                if random.random() < 0.3:
                    self.add_sparkle(sx, sy)

        # 3. Snowflakes (Wider spread)
        if random.random() < 0.4:
            self.add_snowflake(wx + random.randint(-120, 120), wy - random.randint(20, 120))
            
        self._update_and_draw_particles(frame)
        return frame

    def draw_projectile(self, frame, x, y):
        # Draw traveling ice blast
        self.add_mist(x + random.randint(-15, 15), y + random.randint(-15, 15))
        self.add_mist(x + random.randint(-15, 15), y + random.randint(-15, 15))
        
        if random.random() < 0.5:
            self.add_snowflake(x, y)
        if random.random() < 0.6:
            self.add_sparkle(x + random.randint(-25, 25), y + random.randint(-25, 25))
            
        # Central ice crystal
        pts = np.array([
            [int(x), int(y - 20)],
            [int(x + 15), int(y)],
            [int(x), int(y + 20)],
            [int(x - 15), int(y)]
        ], np.int32)
        cv2.fillPoly(frame, [pts], (255, 255, 180))
        cv2.polylines(frame, [pts], True, (255, 255, 255), 2)

        self._update_and_draw_particles(frame)
        return frame

    def _update_and_draw_particles(self, frame):
        overlay = np.zeros_like(frame)
        
        # Mist
        for m in self.mist_particles:
            m['x'] += m['speed_x']
            m['y'] += m['speed_y']
            m['life'] -= 0.04
            if m['life'] > 0:
                cv2.circle(overlay, (int(m['x']), int(m['y'])), int(m['size'] * m['life']), (255, 255, 150), -1)
        cv2.GaussianBlur(overlay, (31, 31), 0, dst=overlay)
        cv2.add(frame, overlay, dst=frame)
        
        # Snowflakes (Procedural 6-arm)
        for s in self.snowflakes:
            s['x'] += s['speed_x']
            s['y'] += s['speed_y']
            s['rotation'] += s['rot_speed']
            s['life'] -= 0.03
            if s['life'] > 0:
                cx, cy = int(s['x']), int(s['y'])
                size = int(s['size'] * s['life'])
                for i in range(6):
                    angle = s['rotation'] + (i * math.pi / 3)
                    ex = cx + int(math.cos(angle) * size)
                    ey = cy + int(math.sin(angle) * size)
                    cv2.line(frame, (cx, cy), (ex, ey), (255, 255, 220), 2)
        
        # 4-point Sparkles
        for sp in self.sparkles:
            sp['life'] -= sp['decay']
            if sp['life'] > 0:
                cx, cy = int(sp['x']), int(sp['y'])
                size = int(sp['size'] * sp['life'])
                cv2.line(frame, (cx - size, cy), (cx + size, cy), (255, 255, 255), 2)
                cv2.line(frame, (cx, cy - size), (cx, cy + size), (255, 255, 255), 2)
                
        self.mist_particles = [m for m in self.mist_particles if m['life'] > 0]
        self.snowflakes = [s for s in self.snowflakes if s['life'] > 0]
        self.sparkles = [sp for sp in self.sparkles if sp['life'] > 0]
