import math

class SpellProjectile:
    def __init__(self, start_x, start_y, target_x, target_y, duration=0.5):
        self.x = float(start_x)
        self.y = float(start_y)
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.distance = math.hypot(dx, dy)
        
        self.speed = self.distance / duration if duration > 0 else 0
        
        if self.distance > 0:
            self.vx = (dx / self.distance) * self.speed
            self.vy = (dy / self.distance) * self.speed
        else:
            self.vx = 0
            self.vy = 0
            
        self.active = True
        self.reached_target = False

    def update(self, dt):
        if not self.active:
            return
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Check if reached target
        dist_to_target = math.hypot(self.target_x - self.x, self.target_y - self.y)
        if dist_to_target < (self.speed * dt) * 1.5 or dist_to_target < 10:
            self.reached_target = True
            self.active = False
