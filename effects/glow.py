import cv2
import numpy as np


class GlowRenderer:
    """
    Utility class for creating and blending luminous magical glow effects,
    multi-stop elemental radial gradients, and additive light overlays.
    """
    _glow_cache = {}

    @classmethod
    def get_radial_glow(cls, radius, color, center_intensity=1.0, falloff=2.0):
        """
        Returns a cached radial glow sprite (BGR uint8 image) with smooth falloff.
        color: tuple (B, G, R) with values in range 0-255.
        """
        key = (int(radius), color, round(center_intensity, 2), round(falloff, 2))
        if key in cls._glow_cache:
            return cls._glow_cache[key]

        r = max(2, int(radius))
        size = r * 2 + 1
        y, x = np.ogrid[-r:r + 1, -r:r + 1]
        dist = np.sqrt(x * x + y * y)

        normalized = np.clip(dist / r, 0, 1)
        intensity = np.power(1.0 - normalized, falloff) * center_intensity
        intensity[dist > r] = 0

        glow = np.zeros((size, size, 3), dtype=np.float32)
        for c in range(3):
            glow[:, :, c] = color[c] * intensity

        glow = np.clip(glow, 0, 255).astype(np.uint8)

        if len(cls._glow_cache) > 250:
            cls._glow_cache.clear()

        cls._glow_cache[key] = glow
        return glow

    @classmethod
    def get_multistop_glow(cls, radius, stops, center_intensity=1.0):
        """
        Generates a multi-stop radial glow.
        stops: list of tuples (pos_ratio, (B, G, R)) from pos 0.0 (center) to 1.0 (edge).
        Example for fire:
        [(0.0, (255, 255, 255)), (0.2, (100, 230, 255)), (0.5, (20, 120, 255)), (0.8, (10, 30, 200)), (1.0, (0, 0, 0))]
        """
        key = (int(radius), tuple((round(p, 2), c) for p, c in stops), round(center_intensity, 2))
        if key in cls._glow_cache:
            return cls._glow_cache[key]

        r = max(2, int(radius))
        size = r * 2 + 1
        y, x = np.ogrid[-r:r + 1, -r:r + 1]
        dist = np.sqrt(x * x + y * y)
        norm_dist = np.clip(dist / r, 0.0, 1.0)

        # Interpolate across stops
        glow = np.zeros((size, size, 3), dtype=np.float32)

        stops = sorted(stops, key=lambda s: s[0])
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p1 <= p0:
                continue

            mask = (norm_dist >= p0) & (norm_dist <= p1)
            t = (norm_dist - p0) / (p1 - p0)
            # Smooth Hermite interpolation
            t_smooth = t * t * (3.0 - 2.0 * t)

            for c in range(3):
                interp_c = (c0[c] * (1.0 - t_smooth) + c1[c] * t_smooth) * center_intensity
                glow[:, :, c] = np.where(mask, interp_c, glow[:, :, c])

        glow[dist > r] = 0
        glow = np.clip(glow, 0, 255).astype(np.uint8)

        if len(cls._glow_cache) > 250:
            cls._glow_cache.clear()

        cls._glow_cache[key] = glow
        return glow

    @staticmethod
    def draw_additive(frame, sprite, center_x, center_y, intensity=1.0):
        sh, sw = sprite.shape[:2]
        fh, fw = frame.shape[:2]

        cx = int(center_x)
        cy = int(center_y)

        x1 = cx - sw // 2
        y1 = cy - sh // 2
        x2 = x1 + sw
        y2 = y1 + sh

        fx1 = max(0, x1)
        fy1 = max(0, y1)
        fx2 = min(fw, x2)
        fy2 = min(fh, y2)

        if fx1 >= fx2 or fy1 >= fy2:
            return

        sx1 = fx1 - x1
        sy1 = fy1 - y1
        sx2 = sx1 + (fx2 - fx1)
        sy2 = sy1 + (fy2 - fy1)

        sprite_crop = sprite[sy1:sy2, sx1:sx2]
        if intensity != 1.0:
            sprite_crop = cv2.multiply(sprite_crop, np.array([intensity, intensity, intensity], dtype=np.float32))
            sprite_crop = np.clip(sprite_crop, 0, 255).astype(np.uint8)

        frame_roi = frame[fy1:fy2, fx1:fx2]
        cv2.add(frame_roi, sprite_crop, dst=frame_roi)

    @staticmethod
    def draw_glowing_circle(frame, center, radius, color, glow_color=None, glow_radius=None, intensity=1.0):
        if glow_color is None:
            glow_color = color
        if glow_radius is None:
            glow_radius = radius * 2.5

        glow_sprite = GlowRenderer.get_radial_glow(glow_radius, glow_color, center_intensity=0.8 * intensity)
        GlowRenderer.draw_additive(frame, glow_sprite, center[0], center[1])
        cv2.circle(frame, (int(center[0]), int(center[1])), max(1, int(radius)), color, -1, cv2.LINE_AA)

    @staticmethod
    def draw_glowing_line(frame, pt1, pt2, color, thickness=2, glow_color=None, glow_thickness=6):
        if glow_color is None:
            glow_color = tuple(min(255, int(c * 0.6)) for c in color)

        glow_buf = np.zeros_like(frame)
        cv2.line(glow_buf, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), glow_color, glow_thickness, cv2.LINE_AA)
        glow_buf = cv2.GaussianBlur(glow_buf, (7, 7), 0)
        cv2.add(frame, glow_buf, dst=frame)
        cv2.line(frame, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), color, thickness, cv2.LINE_AA)
