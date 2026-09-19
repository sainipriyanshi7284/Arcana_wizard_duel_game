import cv2
import numpy as np
import random
import math
from effects.glow import GlowRenderer


class Particle:
    __slots__ = (
        'x', 'y', 'vx', 'vy', 'life', 'max_life', 'start_size', 'end_size',
        'start_color', 'end_color', 'particle_type', 'rotation', 'rot_speed',
        'turbulence_phase', 'turbulence_speed', 'vortex_center', 'vortex_strength'
    )

    def __init__(self, x, y, vx, vy, life, start_size, end_size,
                 start_color, end_color, particle_type="ember",
                 rotation=0.0, rot_speed=0.0, vortex_center=None, vortex_strength=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.start_size = float(start_size)
        self.end_size = float(end_size)
        self.start_color = start_color
        self.end_color = end_color
        self.particle_type = particle_type
        self.rotation = float(rotation)
        self.rot_speed = float(rot_speed)
        self.turbulence_phase = random.uniform(0, math.pi * 2)
        self.turbulence_speed = random.uniform(4.0, 9.0)
        self.vortex_center = vortex_center
        self.vortex_strength = float(vortex_strength)


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self._snowflake_cache = {}

    def _get_snowflake_sprite(self, size, color):
        s = max(8, int(size))
        key = (s, color)
        if key in self._snowflake_cache:
            return self._snowflake_cache[key]

        dim = s * 2 + 7
        sprite = np.zeros((dim, dim, 3), dtype=np.uint8)
        cx, cy = dim // 2, dim // 2

        # Draw 6 main crystal arms
        for i in range(6):
            angle = i * (math.pi / 3.0)
            ex = int(cx + math.cos(angle) * s)
            ey = int(cy + math.sin(angle) * s)
            cv2.line(sprite, (cx, cy), (ex, ey), color, 1, cv2.LINE_AA)

            # Primary outer V-branches
            b1_dist = s * 0.65
            bx1 = cx + math.cos(angle) * b1_dist
            by1 = cy + math.sin(angle) * b1_dist
            for b_off in [-0.78, 0.78]:
                ba = angle + b_off
                blen = s * 0.38
                cv2.line(sprite, (int(bx1), int(by1)),
                         (int(bx1 + math.cos(ba) * blen), int(by1 + math.sin(ba) * blen)),
                         color, 1, cv2.LINE_AA)

            # Secondary inner small V-branches
            b2_dist = s * 0.35
            bx2 = cx + math.cos(angle) * b2_dist
            by2 = cy + math.sin(angle) * b2_dist
            for b_off in [-0.78, 0.78]:
                ba = angle + b_off
                blen = s * 0.22
                cv2.line(sprite, (int(bx2), int(by2)),
                         (int(bx2 + math.cos(ba) * blen), int(by2 + math.sin(ba) * blen)),
                         color, 1, cv2.LINE_AA)

        # Center crystal core
        cv2.circle(sprite, (cx, cy), max(1, s // 5), (255, 255, 255), -1)

        if len(self._snowflake_cache) > 120:
            self._snowflake_cache.clear()

        self._snowflake_cache[key] = sprite
        return sprite

    def emit_fire_ember(self, cx, cy, radius_range=(10, 55)):
        """
        Emits an ember particle that swirls around (cx, cy) and ascends.
        """
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(radius_range[0], radius_range[1])
        x = cx + math.cos(angle) * dist
        y = cy + math.sin(angle) * dist

        # Tangential vortex speed + upward thermal buoyancy
        tangent_speed = random.uniform(80, 180)
        vx = -math.sin(angle) * tangent_speed + random.uniform(-20, 20)
        vy = math.cos(angle) * (tangent_speed * 0.4) - random.uniform(60, 200)

        life = random.uniform(0.5, 1.4)
        start_size = random.uniform(3.5, 7.5)
        end_size = random.uniform(0.5, 2.0)

        # Bright white/gold to vibrant orange-red to dark crimson
        start_color = (random.randint(120, 220), random.randint(230, 255), 255)
        end_color = (5, 30, random.randint(190, 255))

        p = Particle(x, y, vx, vy, life, start_size, end_size,
                     start_color, end_color, particle_type="ember",
                     vortex_center=(cx, cy), vortex_strength=random.uniform(40, 120))
        self.particles.append(p)

    def emit_snowflake(self, cx, cy, radius_range=(20, 95)):
        """
        Emits an intricate crystalline snowflake drifting in the vortex.
        """
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(radius_range[0], radius_range[1])
        x = cx + math.cos(angle) * dist
        y = cy + math.sin(angle) * dist

        tangent_speed = random.uniform(30, 90)
        vx = -math.sin(angle) * tangent_speed + random.uniform(-15, 15)
        vy = math.cos(angle) * (tangent_speed * 0.3) + random.uniform(-10, 30)

        life = random.uniform(1.2, 2.8)
        start_size = random.uniform(8, 16)
        end_size = random.uniform(5, 11)

        start_color = (255, 255, 255)
        end_color = (255, 220, 100)

        p = Particle(x, y, vx, vy, life, start_size, end_size,
                     start_color, end_color, particle_type="snowflake",
                     rotation=random.uniform(0, 360),
                     rot_speed=random.uniform(-120, 120),
                     vortex_center=(cx, cy), vortex_strength=random.uniform(20, 60))
        self.particles.append(p)

    def emit_sparkle(self, cx, cy, color, radius=35):
        """
        Emits a twinkling diamond sparkle / magical dust particle.
        """
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(0, radius)
        x = cx + math.cos(angle) * dist
        y = cy + math.sin(angle) * dist

        vx = random.uniform(-15, 15)
        vy = random.uniform(-15, 15)
        life = random.uniform(0.3, 0.8)
        size = random.uniform(2, 4.5)

        p = Particle(x, y, vx, vy, life, size, 0.5,
                     (255, 255, 255), color, particle_type="sparkle")
        self.particles.append(p)

    def emit_spark(self, x, y, color, speed_range=(90, 280), count=6):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(speed_range[0], speed_range[1])
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.25, 0.65)
            size = random.uniform(2, 5)

            p = Particle(x, y, vx, vy, life, size, 0.5,
                         color, (0, 0, 0), particle_type="spark")
            self.particles.append(p)

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue

            t = p.life / p.max_life
            p.turbulence_phase += dt * p.turbulence_speed

            # Vortex attraction / swirling force
            if p.vortex_center is not None and p.vortex_strength > 0:
                vcx, vcy = p.vortex_center
                dx = p.x - vcx
                dy = p.y - vcy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 5.0:
                    # Inward or circular pull
                    tang_x = -dy / dist
                    tang_y = dx / dist
                    p.vx += tang_x * p.vortex_strength * dt
                    p.vy += tang_y * p.vortex_strength * dt

            if p.particle_type == "ember":
                sway = math.sin(p.turbulence_phase) * 45
                p.x += (p.vx + sway) * dt
                p.y += p.vy * dt
            elif p.particle_type == "snowflake":
                drift = math.sin(p.turbulence_phase) * 22
                p.x += (p.vx + drift) * dt
                p.y += p.vy * dt
                p.rotation += p.rot_speed * dt
            else:
                p.x += p.vx * dt
                p.y += p.vy * dt

            alive.append(p)

        self.particles = alive

    def draw(self, frame):
        fh, fw = frame.shape[:2]

        for p in self.particles:
            t = max(0.0, min(1.0, p.life / p.max_life))
            size = p.start_size * t + p.end_size * (1.0 - t)

            b = int(p.start_color[0] * t + p.end_color[0] * (1.0 - t))
            g = int(p.start_color[1] * t + p.end_color[1] * (1.0 - t))
            r = int(p.start_color[2] * t + p.end_color[2] * (1.0 - t))
            color = (b, g, r)

            px = int(p.x)
            py = int(p.y)

            if px < -25 or px >= fw + 25 or py < -25 or py >= fh + 25:
                continue

            if p.particle_type == "ember":
                glow_radius = int(size * 3.0)
                glow = GlowRenderer.get_radial_glow(glow_radius, color, center_intensity=0.85 * t)
                GlowRenderer.draw_additive(frame, glow, px, py)
                cv2.circle(frame, (px, py), max(1, int(size * 0.75)), (255, 255, 255), -1, cv2.LINE_AA)

            elif p.particle_type == "snowflake":
                sprite = self._get_snowflake_sprite(size, color)
                if abs(p.rotation) > 1.0:
                    sh, sw = sprite.shape[:2]
                    rot_mat = cv2.getRotationMatrix2D((sw / 2, sh / 2), p.rotation, 1.0)
                    sprite = cv2.warpAffine(sprite, rot_mat, (sw, sh), flags=cv2.INTER_LINEAR)

                GlowRenderer.draw_additive(frame, sprite, px, py, intensity=t)
                center_glow = GlowRenderer.get_radial_glow(int(size * 1.8), (255, 220, 100), center_intensity=0.6 * t)
                GlowRenderer.draw_additive(frame, center_glow, px, py)

            elif p.particle_type == "sparkle":
                # Diamond twinkle
                twinkle_t = math.sin(t * math.pi)
                s = max(1, int(size * twinkle_t))
                pts = np.array([
                    [px, py - s * 2], [px + s, py], [px, py + s * 2], [px - s, py]
                ], dtype=np.int32)
                cv2.fillPoly(frame, [pts], (255, 255, 255), lineType=cv2.LINE_AA)
                glow = GlowRenderer.get_radial_glow(int(s * 3), color, center_intensity=0.9 * twinkle_t)
                GlowRenderer.draw_additive(frame, glow, px, py)

            elif p.particle_type == "spark":
                cv2.circle(frame, (px, py), max(1, int(size)), color, -1, cv2.LINE_AA)
                glow = GlowRenderer.get_radial_glow(int(size * 2.8), color, center_intensity=0.7 * t)
                GlowRenderer.draw_additive(frame, glow, px, py)
