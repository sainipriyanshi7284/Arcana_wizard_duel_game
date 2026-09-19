import cv2
import numpy as np
import random
import math
from effects.glow import GlowRenderer
from effects.particles import ParticleSystem
from effects.magic_circle import MagicCircleRenderer


class FlamePuff:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'growth', 'seed', 'flame_type')

    def __init__(self, x, y, vx, vy, life, size, growth=1.2, flame_type="core"):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.size = float(size)
        self.growth = float(growth)
        self.seed = random.uniform(0, 100)
        self.flame_type = flame_type


class FireVFX:
    """
    Ultra-Aesthetic, Highly Saturated Cinematic Fire Simulation:
    - Multi-layer chromatic richness (Volcanic Crimson -> Cadmium Orange -> Solar Gold -> Electric Core)
    - Organic sweeping flame tongues licking 180-280px upward from knuckles and fingertips
    - Whirling plasma tendrils wrapping hand and wrist
    - Billowing volumetric puffs with zero washed-out tint
    - Radiant fiery bloom and floating convection spark embers
    """

    def __init__(self):
        self.flames = []
        self.embers = []
        self.time_val = 0.0
        self._flame_puff_cache = {}

    def _get_flame_puff(self, radius, color, core_white=False):
        r = max(5, int(radius))
        key = (r, color, core_white)
        if key in self._flame_puff_cache:
            return self._flame_puff_cache[key]

        size = r * 2 + 1
        y, x = np.ogrid[-r:r + 1, -r:r + 1]
        dist_sq = x * x + y * y
        sigma_sq = (r * 0.44) ** 2

        intensity = np.exp(-dist_sq / (2 * sigma_sq))
        intensity[dist_sq > r * r] = 0

        sprite = np.zeros((size, size, 3), dtype=np.float32)
        for c in range(3):
            sprite[:, :, c] = color[c] * intensity

        if core_white:
            inner_sigma_sq = (r * 0.18) ** 2
            inner_int = np.exp(-dist_sq / (2 * inner_sigma_sq))
            for c in range(3):
                sprite[:, :, c] = np.maximum(sprite[:, :, c], 255.0 * inner_int)

        sprite = np.clip(sprite, 0, 255).astype(np.uint8)
        if len(self._flame_puff_cache) > 400:
            self._flame_puff_cache.clear()
        self._flame_puff_cache[key] = sprite
        return sprite

    def update(self, dt, hand_pts, is_active=True, charge_ratio=0.5):
        self.time_val += dt

        alive_flames = []
        for f in self.flames:
            f.life -= dt
            if f.life <= 0:
                continue

            t = f.life / f.max_life
            f.y += f.vy * dt
            sway = math.sin(self.time_val * 13.0 + f.seed) * (42.0 * (1.0 - t * 0.4))
            f.x += (f.vx + sway) * dt
            f.size += f.growth * dt * 28.0
            alive_flames.append(f)
        self.flames = alive_flames

        alive_embers = []
        for e in self.embers:
            e.life -= dt
            if e.life <= 0:
                continue
            e.y += e.vy * dt
            e.x += (e.vx + math.sin(self.time_val * 8.0 + e.seed) * 32.0) * dt
            alive_embers.append(e)
        self.embers = alive_embers

        if not is_active or not hand_pts:
            return

        if len(hand_pts) >= 21:
            palm = hand_pts[9]
            wrist = hand_pts[0]
            knuckles = [hand_pts[5], hand_pts[9], hand_pts[13], hand_pts[17]]
            tips = [hand_pts[4], hand_pts[8], hand_pts[12], hand_pts[16], hand_pts[20]]
        else:
            palm = hand_pts[0]
            wrist = hand_pts[0]
            knuckles = [hand_pts[0]]
            tips = [hand_pts[0]]

        # 1. Spawn Saturated Volumetric Flame Puffs
        spawn_count = int(14 + charge_ratio * 12)
        for _ in range(spawn_count):
            src = random.choice([palm] * 4 + knuckles * 3 + tips * 2 + [wrist])
            sx = src[0] + random.uniform(-25, 25)
            sy = src[1] + random.uniform(-20, 18)

            vy = -random.uniform(160, 380)
            vx = random.uniform(-45, 45)
            life = random.uniform(0.35, 0.75)
            size = random.uniform(22, 45)
            growth = random.uniform(0.8, 1.7)

            self.flames.append(FlamePuff(sx, sy, vx, vy, life, size, growth, flame_type="core"))

        # 2. Spawn Fingertip Fire Licks
        for tip in tips:
            if random.random() < 0.85:
                tx = tip[0] + random.uniform(-12, 12)
                ty = tip[1] + random.uniform(-10, 8)
                vy = -random.uniform(140, 320)
                vx = random.uniform(-30, 30)
                life = random.uniform(0.3, 0.65)
                size = random.uniform(16, 30)
                self.flames.append(FlamePuff(tx, ty, vx, vy, life, size, growth=1.2, flame_type="tip"))

        # 3. Spawn Rising Spark Embers
        for _ in range(random.randint(4, 9)):
            src = random.choice([palm, wrist] + knuckles + tips)
            ex = src[0] + random.uniform(-35, 35)
            ey = src[1] + random.uniform(-25, 25)
            evy = -random.uniform(180, 480)
            evx = random.uniform(-80, 80)
            elife = random.uniform(0.7, 1.7)
            esize = random.uniform(2.5, 6.0)
            self.embers.append(FlamePuff(ex, ey, evx, evy, elife, esize, growth=-0.3, flame_type="ember"))

    def draw(self, frame, hand_pts, charge_ratio=0.5):
        if not hand_pts:
            return

        palm = hand_pts[9] if len(hand_pts) > 9 else hand_pts[0]
        wrist = hand_pts[0] if len(hand_pts) > 0 else palm
        cx, cy = int(palm[0]), int(palm[1])
        fh, fw = frame.shape[:2]

        # 1. Intense Volcanic Atmospheric Ambient Illumination
        ambient_r = int(170 + charge_ratio * 80)
        ambient_glow = GlowRenderer.get_radial_glow(ambient_r, (0, 55, 255), center_intensity=0.75, falloff=2.4)
        GlowRenderer.draw_additive(frame, ambient_glow, cx, cy - 45)

        # 2. Multi-layer Organic Flame Tongues rendered onto a smoothed buffer
        flame_buf = np.zeros((fh, fw, 3), dtype=np.uint8)

        # Gather anchor points across knuckles, palm, and fingertips
        anchors = []
        if len(hand_pts) >= 21:
            anchors.extend([hand_pts[0], hand_pts[5], hand_pts[9], hand_pts[13], hand_pts[17],
                            hand_pts[4], hand_pts[8], hand_pts[12], hand_pts[16], hand_pts[20]])
        else:
            anchors = [palm]

        num_tongues = 13
        for i in range(num_tongues):
            t_ratio = i / float(num_tongues - 1)
            # Spread tongues organically across hand anchors
            anc_idx = int(t_ratio * (len(anchors) - 1))
            anc = anchors[anc_idx]

            bx = anc[0] + (t_ratio - 0.5) * 50 + math.sin(self.time_val * 8.0 + i * 1.5) * 15
            by = anc[1] + 16

            tongue_h = (170 + charge_ratio * 125) + math.sin(self.time_val * 16.0 + i * 2.3) * 42
            tx = bx + math.sin(self.time_val * 10.0 + i * 1.7) * 40 + math.sin(self.time_val * 21.0 + i) * 14
            ty = by - tongue_h

            w_mid = 26 + math.sin(self.time_val * 12.0 + i) * 8
            mid_y = by - tongue_h * 0.42

            # Outer Saturated Crimson/Ruby Flame Envelope
            pts_crimson = np.array([
                [int(bx - w_mid * 1.25), int(by)],
                [int(bx - w_mid * 1.4), int(mid_y)],
                [int(tx), int(ty - 10)],
                [int(bx + w_mid * 1.4), int(mid_y)],
                [int(bx + w_mid * 1.25), int(by)],
            ], dtype=np.int32)
            cv2.fillPoly(flame_buf, [pts_crimson], (0, 15, 255), lineType=cv2.LINE_AA)

            # Mid Saturated Cadmium Orange Flame Body (B=0 for pure neon saturation!)
            pts_orange = np.array([
                [int(bx - w_mid * 0.85), int(by)],
                [int(bx - w_mid * 0.95), int(mid_y + 8)],
                [int(tx), int(ty + 15)],
                [int(bx + w_mid * 0.95), int(mid_y + 8)],
                [int(bx + w_mid * 0.85), int(by)],
            ], dtype=np.int32)
            cv2.fillPoly(flame_buf, [pts_orange], (0, 105, 255), lineType=cv2.LINE_AA)

            # Inner Saturated Solar Gold Spine
            pts_yellow = np.array([
                [int(bx - w_mid * 0.38), int(by)],
                [int(bx - w_mid * 0.42), int(mid_y + 24)],
                [int(tx), int(ty + 44)],
                [int(bx + w_mid * 0.42), int(mid_y + 24)],
                [int(bx - w_mid * 0.38), int(by)],
            ], dtype=np.int32)
            cv2.fillPoly(flame_buf, [pts_yellow], (5, 195, 255), lineType=cv2.LINE_AA)

        # Smooth tongues to organic thermal plumes
        flame_buf = cv2.GaussianBlur(flame_buf, (25, 25), 0)
        cv2.add(frame, flame_buf, dst=frame)

        # 3. Volumetric Flame Puffs with High Dynamic Blackbody Colors
        for f in self.flames:
            t = max(0.0, min(1.0, f.life / f.max_life))
            if t > 0.82:
                # Saturated Solar Gold
                color = (10, 205, 255)
            elif t > 0.48:
                # Saturated Cadmium Orange
                color = (0, 115, 255)
            elif t > 0.18:
                # Deep Fiery Crimson
                color = (0, 28, 245)
            else:
                # Dark Ruby Smoke
                color = (0, 5, 190)

            puff = self._get_flame_puff(f.size, color, core_white=False)
            GlowRenderer.draw_additive(frame, puff, int(f.x), int(f.y), intensity=min(0.85, t * 1.1))

        # 4. Hand Plasma Tendrils (luminous fiery arcs tracing fingers)
        if len(hand_pts) >= 21:
            for tip_idx in [4, 8, 12, 16, 20]:
                tip = hand_pts[tip_idx]
                arc_pts = []
                steps = 6
                for s in range(steps + 1):
                    alpha = s / float(steps)
                    ax = int(palm[0] * (1 - alpha) + tip[0] * alpha + math.sin(self.time_val * 14.0 + s + tip_idx) * 10)
                    ay = int(palm[1] * (1 - alpha) + tip[1] * alpha + math.cos(self.time_val * 14.0 + s + tip_idx) * 8)
                    arc_pts.append((ax, ay))
                for j in range(len(arc_pts) - 1):
                    cv2.line(frame, arc_pts[j], arc_pts[j + 1], (0, 140, 255), 2, cv2.LINE_AA)
                    cv2.line(frame, arc_pts[j], arc_pts[j + 1], (100, 240, 255), 1, cv2.LINE_AA)

        # 5. Concentrated White-Hot Incandescent Core at Palm
        core_r = int(24 + charge_ratio * 12)
        core_glow = self._get_flame_puff(core_r, (70, 235, 255), core_white=True)
        GlowRenderer.draw_additive(frame, core_glow, cx, cy - 8, intensity=1.0)

        # 6. Saturated Rising Spark Embers with Convection Physics
        for e in self.embers:
            t = max(0.0, min(1.0, e.life / e.max_life))
            size = max(1, int(e.size * t))
            ex, ey = int(e.x), int(e.y)

            ecolor = (25, 240, 255) if t > 0.45 else (0, 95, 255)
            glow = GlowRenderer.get_radial_glow(int(size * 3.5), ecolor, center_intensity=0.95 * t)
            GlowRenderer.draw_additive(frame, glow, ex, ey)
            cv2.circle(frame, (ex, ey), size, (255, 255, 255), -1, cv2.LINE_AA)


class IceVFX:
    """
    Ultra-Aesthetic, Highly Saturated Cryogenic Frost & Blizzard Simulation:
    - Pure saturated electric cyan & glacial azure (R=0 for max saturation!)
    - Crystalline ice spikes and faceted frost shards growing from fingers
    - Soaring frost plumes streaming 180-260px upward from victory fingers
    - Dense blizzard of tumbling 6-point snowflakes and diamond ice sparkles
    - Radiant glacial blue atmospheric illumination
    """

    def __init__(self):
        self.vapors = []
        self.snowflakes = []
        self.sparkles = []
        self.time_val = 0.0
        self._vapor_cache = {}
        self._snowflake_cache = {}

    def _get_vapor_puff(self, radius, color):
        r = max(5, int(radius))
        key = (r, color)
        if key in self._vapor_cache:
            return self._vapor_cache[key]

        size = r * 2 + 1
        y, x = np.ogrid[-r:r + 1, -r:r + 1]
        dist_sq = x * x + y * y
        sigma_sq = (r * 0.44) ** 2

        intensity = np.exp(-dist_sq / (2 * sigma_sq))
        intensity[dist_sq > r * r] = 0

        sprite = np.zeros((size, size, 3), dtype=np.float32)
        for c in range(3):
            sprite[:, :, c] = color[c] * intensity

        sprite = np.clip(sprite, 0, 255).astype(np.uint8)
        if len(self._vapor_cache) > 400:
            self._vapor_cache.clear()
        self._vapor_cache[key] = sprite
        return sprite

    def _get_snowflake_sprite(self, size, color):
        s = max(9, int(size))
        key = (s, color)
        if key in self._snowflake_cache:
            return self._snowflake_cache[key]

        dim = s * 2 + 7
        sprite = np.zeros((dim, dim, 3), dtype=np.uint8)
        cx, cy = dim // 2, dim // 2

        for i in range(6):
            angle = i * (math.pi / 3.0)
            ex = int(cx + math.cos(angle) * s)
            ey = int(cy + math.sin(angle) * s)
            cv2.line(sprite, (cx, cy), (ex, ey), color, 1, cv2.LINE_AA)

            b1_dist = s * 0.65
            bx1 = cx + math.cos(angle) * b1_dist
            by1 = cy + math.sin(angle) * b1_dist
            for b_off in [-0.78, 0.78]:
                ba = angle + b_off
                blen = s * 0.38
                cv2.line(sprite, (int(bx1), int(by1)),
                         (int(bx1 + math.cos(ba) * blen), int(by1 + math.sin(ba) * blen)),
                         color, 1, cv2.LINE_AA)

        cv2.circle(sprite, (cx, cy), max(1, s // 5), (255, 255, 255), -1)
        if len(self._snowflake_cache) > 150:
            self._snowflake_cache.clear()
        self._snowflake_cache[key] = sprite
        return sprite

    def update(self, dt, hand_pts, is_active=True, charge_ratio=0.5):
        self.time_val += dt

        alive_vapors = []
        for v in self.vapors:
            v.life -= dt
            if v.life <= 0:
                continue
            v.y += v.vy * dt
            v.x += (v.vx + math.sin(self.time_val * 8.0 + v.seed) * 25.0) * dt
            v.size += v.growth * dt * 24.0
            alive_vapors.append(v)
        self.vapors = alive_vapors

        alive_snow = []
        for s in self.snowflakes:
            s['life'] -= dt
            if s['life'] <= 0:
                continue
            s['x'] += (s['vx'] + math.sin(self.time_val * 4.5 + s['seed']) * 20.0) * dt
            s['y'] += s['vy'] * dt
            s['rot'] += s['rot_speed'] * dt
            alive_snow.append(s)
        self.snowflakes = alive_snow

        alive_sparkles = []
        for sp in self.sparkles:
            sp['life'] -= dt
            if sp['life'] > 0:
                alive_sparkles.append(sp)
        self.sparkles = alive_sparkles

        if not is_active or not hand_pts:
            return

        palm = hand_pts[9] if len(hand_pts) > 9 else hand_pts[0]
        wrist = hand_pts[0]
        v_tips = [hand_pts[8], hand_pts[12]] if len(hand_pts) >= 21 else [palm]

        num_vapors = int(11 + charge_ratio * 9)
        for _ in range(num_vapors):
            src = random.choice(v_tips * 4 + [palm] * 2 + [wrist])
            sx = src[0] + random.uniform(-26, 26)
            sy = src[1] + random.uniform(-22, 20)
            vy = -random.uniform(80, 220)
            vx = random.uniform(-35, 35)
            life = random.uniform(0.45, 0.95)
            size = random.uniform(22, 48)
            self.vapors.append(FlamePuff(sx, sy, vx, vy, life, size, growth=1.3, flame_type="ice_vapor"))

        if random.random() < (0.75 + charge_ratio * 0.25):
            src = random.choice(v_tips + [palm])
            self.snowflakes.append({
                'x': src[0] + random.uniform(-55, 55),
                'y': src[1] + random.uniform(-45, 45),
                'vx': random.uniform(-25, 25),
                'vy': random.uniform(-15, 35),
                'rot': random.uniform(0, 360),
                'rot_speed': random.uniform(-110, 110),
                'size': random.uniform(10, 22),
                'life': random.uniform(1.4, 2.8),
                'max_life': 2.6,
                'seed': random.uniform(0, 100),
            })

        # Diamond glint sparkles
        if random.random() < 0.6:
            src = random.choice(v_tips + [palm])
            self.sparkles.append({
                'x': src[0] + random.uniform(-40, 40),
                'y': src[1] + random.uniform(-40, 30),
                'size': random.uniform(4, 9),
                'life': random.uniform(0.3, 0.6),
                'max_life': 0.6
            })

    def draw(self, frame, hand_pts, charge_ratio=0.5):
        if not hand_pts:
            return

        palm = hand_pts[9] if len(hand_pts) > 9 else hand_pts[0]
        cx, cy = int(palm[0]), int(palm[1])
        fh, fw = frame.shape[:2]

        # 1. Glacial Atmospheric Cyan Illumination
        ambient_r = int(160 + charge_ratio * 75)
        frost_glow = GlowRenderer.get_radial_glow(ambient_r, (255, 195, 0), center_intensity=0.7, falloff=2.4)
        GlowRenderer.draw_additive(frame, frost_glow, cx, cy - 40)

        # 2. Billowing Cryogenic Vapor Plumes
        for v in self.vapors:
            t = max(0.0, min(1.0, v.life / v.max_life))
            if t > 0.65:
                color = (255, 235, 15)
            elif t > 0.28:
                color = (255, 140, 0)
            else:
                color = (235, 70, 0)
            sprite = self._get_vapor_puff(v.size, color)
            GlowRenderer.draw_additive(frame, sprite, int(v.x), int(v.y), intensity=min(0.85, t * 1.05))

        # 3. Crystalline Ice Spikes jutting from Victory Fingers
        if len(hand_pts) >= 21:
            for tip_idx in [8, 12]:
                tip = hand_pts[tip_idx]
                prev = hand_pts[tip_idx - 1]
                dx = tip[0] - prev[0]
                dy = tip[1] - prev[1]
                dist = max(1.0, math.sqrt(dx * dx + dy * dy))
                nx, ny = dx / dist, dy / dist
                perp_x, perp_y = -ny, nx

                # Faceted crystal spike
                spike_len = (95 + charge_ratio * 60) + math.sin(self.time_val * 9.0 + tip_idx) * 12
                tip_x = int(tip[0] + nx * spike_len)
                tip_y = int(tip[1] + ny * spike_len)
                base_w = 18

                # Left facet (Glacial Azure)
                poly_left = np.array([
                    [int(tip[0]), int(tip[1])],
                    [int(tip[0] + perp_x * base_w), int(tip[1] + perp_y * base_w)],
                    [tip_x, tip_y]
                ], dtype=np.int32)
                cv2.fillPoly(frame, [poly_left], (255, 130, 0), lineType=cv2.LINE_AA)

                # Right facet (Electric Cyan)
                poly_right = np.array([
                    [int(tip[0]), int(tip[1])],
                    [int(tip[0] - perp_x * base_w), int(tip[1] - perp_y * base_w)],
                    [tip_x, tip_y]
                ], dtype=np.int32)
                cv2.fillPoly(frame, [poly_right], (255, 225, 20), lineType=cv2.LINE_AA)

                # Spine highlight (White-hot crystal ridge)
                cv2.line(frame, (int(tip[0]), int(tip[1])), (tip_x, tip_y), (255, 255, 255), 2, cv2.LINE_AA)

                # Diamond star emblem at the apex of the ice crystal
                MagicCircleRenderer.draw_ornate_star_emblem(
                    frame, tip_x, tip_y, size=12,
                    color=(255, 245, 180), glow_color=(255, 200, 0)
                )

                # Plumes of frost breath from the spike
                for s in range(4):
                    flen = spike_len * 0.4 + s * 22 + math.sin(self.time_val * 12.0 + s) * 10
                    fx = int(tip[0] + nx * flen)
                    fy = int(tip[1] + ny * flen)
                    puff = self._get_vapor_puff(18 + s * 6, (255, 245, 140))
                    GlowRenderer.draw_additive(frame, puff, fx, fy, intensity=0.75)

        # 4. Saturated Floating 6-point Snowflakes
        for s in self.snowflakes:
            t = max(0.0, min(1.0, s['life'] / s['max_life']))
            size = s['size'] * t
            sprite = self._get_snowflake_sprite(size, (255, 245, 150))
            if abs(s['rot']) > 1.0:
                sh, sw = sprite.shape[:2]
                mat = cv2.getRotationMatrix2D((sw / 2, sh / 2), s['rot'], 1.0)
                sprite = cv2.warpAffine(sprite, mat, (sw, sh), flags=cv2.INTER_LINEAR)

            GlowRenderer.draw_additive(frame, sprite, int(s['x']), int(s['y']), intensity=t)

        # 5. Twinkling Diamond Sparkles
        for sp in self.sparkles:
            t = max(0.0, min(1.0, sp['life'] / sp['max_life']))
            s = int(sp['size'] * math.sin(t * math.pi))
            if s >= 2:
                sx, sy = int(sp['x']), int(sp['y'])
                cv2.line(frame, (sx - s, sy), (sx + s, sy), (255, 255, 255), 1, cv2.LINE_AA)
                cv2.line(frame, (sx, sy - s), (sx, sy + s), (255, 255, 255), 1, cv2.LINE_AA)
                glow = GlowRenderer.get_radial_glow(s * 2, (255, 220, 50), center_intensity=0.8)
                GlowRenderer.draw_additive(frame, glow, sx, sy)


class ShieldVFX:
    def __init__(self):
        self.pulse = 0.0

    def update(self, dt, hand_pts, is_active=True, charge_ratio=0.5):
        self.pulse += dt * 4.0

    def draw(self, frame, hand_pts, charge_ratio=0.5):
        if not hand_pts:
            return
        cx, cy = int(hand_pts[9][0]), int(hand_pts[9][1]) if len(hand_pts) > 9 else (int(hand_pts[0][0]), int(hand_pts[0][1]))
        r = 90 + charge_ratio * 40
        MagicCircleRenderer.draw_hex_shield(frame, cx, cy, radius=r, pulse=self.pulse, color=(255, 220, 100))


class LightningVFX:
    def __init__(self):
        self.particle_system = ParticleSystem()
        self.timer = 0.0

    def update(self, dt, hand_pts, is_active=True, charge_ratio=0.5):
        self.particle_system.update(dt)
        self.timer += dt
        if not is_active or not hand_pts:
            return
        cx, cy = hand_pts[8] if len(hand_pts) > 8 else hand_pts[0]
        if random.random() < 0.5:
            self.particle_system.emit_spark(cx, cy, color=(255, 240, 180), speed_range=(110, 300), count=5)

    def draw(self, frame, hand_pts, charge_ratio=0.5):
        if not hand_pts:
            return
        cx, cy = int(hand_pts[8][0]), int(hand_pts[8][1]) if len(hand_pts) > 8 else (int(hand_pts[0][0]), int(hand_pts[0][1]))
        r = 80 + charge_ratio * 40

        glow = GlowRenderer.get_radial_glow(int(r * 1.6), (255, 200, 120), center_intensity=0.85)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

        wrist = hand_pts[0]
        tips = [hand_pts[i] for i in [4, 8, 12, 16, 20]] if len(hand_pts) >= 21 else [hand_pts[0]]
        for tip in tips:
            cur_x, cur_y = wrist[0], wrist[1]
            bolt_pts = [(int(cur_x), int(cur_y))]
            segments = 5
            for s in range(segments):
                t = (s + 1) / float(segments)
                bx = int(wrist[0] * (1 - t) + tip[0] * t + random.randint(-15, 15))
                by = int(wrist[1] * (1 - t) + tip[1] * t + random.randint(-15, 15))
                bolt_pts.append((bx, by))
            for i in range(len(bolt_pts) - 1):
                cv2.line(frame, bolt_pts[i], bolt_pts[i+1], (255, 240, 160), 2, cv2.LINE_AA)
                cv2.line(frame, bolt_pts[i], bolt_pts[i+1], (255, 255, 255), 1, cv2.LINE_AA)

        self.particle_system.draw(frame)


class WindVFX:
    def __init__(self):
        self.angle = 0.0

    def update(self, dt, hand_pts, is_active=True, charge_ratio=0.5):
        self.angle += dt * 6.5

    def draw(self, frame, hand_pts, charge_ratio=0.5):
        if not hand_pts:
            return
        cx, cy = int(hand_pts[4][0]), int(hand_pts[4][1]) if len(hand_pts) > 4 else (int(hand_pts[0][0]), int(hand_pts[0][1]))
        r = 75 + charge_ratio * 35

        glow = GlowRenderer.get_radial_glow(int(r * 1.7), (150, 255, 180), center_intensity=0.55)
        GlowRenderer.draw_additive(frame, glow, cx, cy)


class Projectile:
    def __init__(self, start_pos, target_pos, spell_name, damage):
        self.x, self.y = float(start_pos[0]), float(start_pos[1])
        self.target_x, self.target_y = float(target_pos[0]), float(target_pos[1])
        self.spell_name = spell_name
        self.damage = damage
        self.speed = 950.0
        self.active = True
        self.trail_system = ParticleSystem()

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = max(1.0, math.sqrt(dx * dx + dy * dy))
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed

    def update(self, dt):
        self.trail_system.update(dt)
        self.x += self.vx * dt
        self.y += self.vy * dt

        if "Fire" in self.spell_name:
            self.trail_system.emit_fire_ember(self.x, self.y, radius_range=(4, 18))
        elif "Ice" in self.spell_name:
            self.trail_system.emit_snowflake(self.x, self.y, radius_range=(4, 20))
        else:
            self.trail_system.emit_spark(self.x, self.y, (255, 255, 100), speed_range=(20, 80), count=3)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        if math.sqrt(dx * dx + dy * dy) < 45.0:
            self.active = False
            return True
        return False

    def draw(self, frame):
        self.trail_system.draw(frame)
        cx, cy = int(self.x), int(self.y)

        if "Fire" in self.spell_name:
            glow = GlowRenderer.get_radial_glow(48, (0, 140, 255), center_intensity=1.0)
            GlowRenderer.draw_additive(frame, glow, cx, cy)
            cv2.circle(frame, (cx, cy), 18, (10, 220, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 9, (255, 255, 255), -1, cv2.LINE_AA)
        elif "Ice" in self.spell_name:
            glow = GlowRenderer.get_radial_glow(48, (255, 210, 0), center_intensity=1.0)
            GlowRenderer.draw_additive(frame, glow, cx, cy)
            cv2.circle(frame, (cx, cy), 15, (255, 240, 120), -1, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 8, (255, 255, 255), -1, cv2.LINE_AA)
        else:
            glow = GlowRenderer.get_radial_glow(38, (255, 240, 120), center_intensity=0.95)
            GlowRenderer.draw_additive(frame, glow, cx, cy)
            cv2.circle(frame, (cx, cy), 12, (255, 255, 255), -1, cv2.LINE_AA)


class ProjectileManager:
    def __init__(self):
        self.projectiles = []
        self.impacts = []
        self.impact_particles = ParticleSystem()

    def spawn(self, start_pos, target_pos, spell_name, damage):
        self.projectiles.append(Projectile(start_pos, target_pos, spell_name, damage))

    def trigger_impact(self, pos, spell_name):
        cx, cy = pos
        if "Fire" in spell_name:
            color = (0, 140, 255)
        elif "Ice" in spell_name:
            color = (255, 210, 0)
        else:
            color = (255, 240, 150)
        self.impact_particles.emit_spark(cx, cy, color=color, speed_range=(160, 420), count=40)
        self.impacts.append({'pos': pos, 'time': 0.45, 'color': color})

    def update(self, dt):
        self.impact_particles.update(dt)

        alive_proj = []
        for p in self.projectiles:
            hit = p.update(dt)
            if hit:
                self.trigger_impact((p.x, p.y), p.spell_name)
            elif p.active:
                alive_proj.append(p)
        self.projectiles = alive_proj

        alive_impacts = []
        for imp in self.impacts:
            imp['time'] -= dt
            if imp['time'] > 0:
                alive_impacts.append(imp)
        self.impacts = alive_impacts

    def draw(self, frame):
        for p in self.projectiles:
            p.draw(frame)

        self.impact_particles.draw(frame)

        for imp in self.impacts:
            cx, cy = int(imp['pos'][0]), int(imp['pos'][1])
            glow = GlowRenderer.get_radial_glow(95, imp['color'], center_intensity=imp['time'] * 3.2)
            GlowRenderer.draw_additive(frame, glow, cx, cy)
