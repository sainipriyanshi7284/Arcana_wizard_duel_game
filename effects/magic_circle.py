import cv2
import numpy as np
import math
from effects.glow import GlowRenderer


class MagicCircleRenderer:
    """
    Renders procedural arcane geometries: 4-pointed star emblems,
    rotating runic circles, and hexagonal energy shields.
    """

    @staticmethod
    def draw_ornate_star_emblem(frame, cx, cy, size=18, color=(100, 200, 255), glow_color=(50, 140, 255)):
        """
        Draws the ornate 4-pointed golden/mystical diamond star emblem
        seen on the center divider in the reference image.
        color: (B, G, R) gold/amber or cyan
        """
        cx = int(cx)
        cy = int(cy)
        s = int(size)

        # Soft radial glow behind the emblem
        glow = GlowRenderer.get_radial_glow(s * 2, glow_color, center_intensity=0.9)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

        # 4-pointed primary star points
        pts_star = np.array([
            [cx, cy - s],                      # Top tip
            [cx + int(s * 0.22), cy - int(s * 0.22)],
            [cx + s, cy],                      # Right tip
            [cx + int(s * 0.22), cy + int(s * 0.22)],
            [cx, cy + s],                      # Bottom tip
            [cx - int(s * 0.22), cy + int(s * 0.22)],
            [cx - s, cy],                      # Left tip
            [cx - int(s * 0.22), cy - int(s * 0.22)],
        ], dtype=np.int32)

        # Draw filled outer star
        cv2.fillPoly(frame, [pts_star], color, lineType=cv2.LINE_AA)

        # 4-pointed secondary diagonal star (smaller)
        s2 = int(s * 0.55)
        pts_diag = np.array([
            [cx, cy - s2],
            [cx + s2, cy],
            [cx, cy + s2],
            [cx - s2, cy],
        ], dtype=np.int32)
        # Rotated 45 degrees
        diag_pts = []
        for pt in pts_diag:
            dx = pt[0] - cx
            dy = pt[1] - cy
            rx = int(cx + (dx * 0.707 - dy * 0.707))
            ry = int(cy + (dx * 0.707 + dy * 0.707))
            diag_pts.append([rx, ry])
        cv2.fillPoly(frame, [np.array(diag_pts, dtype=np.int32)], (200, 240, 255), lineType=cv2.LINE_AA)

        # Bright center diamond / core
        core_s = max(2, int(s * 0.28))
        core_pts = np.array([
            [cx, cy - core_s],
            [cx + core_s, cy],
            [cx, cy + core_s],
            [cx - core_s, cy]
        ], dtype=np.int32)
        cv2.fillPoly(frame, [core_pts], (255, 255, 255), lineType=cv2.LINE_AA)

    @staticmethod
    def draw_arcane_ring(frame, cx, cy, radius, angle, color=(255, 200, 80), num_glyphs=8):
        """
        Draws a rotating arcane magic circle with runes and geometric inscriptions.
        """
        cx = int(cx)
        cy = int(cy)
        r = int(radius)

        if r < 10:
            return

        # Concentric glowing circles
        cv2.circle(frame, (cx, cy), r, color, 1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), int(r * 0.85), color, 1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), int(r * 0.5), color, 1, cv2.LINE_AA)

        # Outer soft glow
        glow = GlowRenderer.get_radial_glow(int(r * 1.3), color, center_intensity=0.4)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

        # Rotating geometric runes / spokes
        for i in range(num_glyphs):
            theta = angle + i * (math.pi * 2 / num_glyphs)
            r1 = r * 0.85
            r2 = r
            x1 = int(cx + math.cos(theta) * r1)
            y1 = int(cy + math.sin(theta) * r1)
            x2 = int(cx + math.cos(theta) * r2)
            y2 = int(cy + math.sin(theta) * r2)
            cv2.line(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

            # Small rune node
            dot_r = r * 0.7
            dx = int(cx + math.cos(theta + 0.15) * dot_r)
            dy = int(cy + math.sin(theta + 0.15) * dot_r)
            cv2.circle(frame, (dx, dy), 2, color, -1, cv2.LINE_AA)

    @staticmethod
    def draw_hex_shield(frame, cx, cy, radius, pulse=1.0, color=(255, 220, 80)):
        """
        Draws an energy shield barrier with hexagonal lattice grid.
        """
        cx = int(cx)
        cy = int(cy)
        r = int(radius * (0.95 + 0.05 * math.sin(pulse)))

        # Shield glow
        glow = GlowRenderer.get_radial_glow(int(r * 1.4), color, center_intensity=0.6)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

        # Main hexagon
        hex_pts = []
        for i in range(6):
            ang = i * (math.pi / 3.0)
            hx = int(cx + math.cos(ang) * r)
            hy = int(cy + math.sin(ang) * r)
            hex_pts.append([hx, hy])

        pts = np.array(hex_pts, dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_AA)

        # Internal honeycomb lines
        for i in range(6):
            ang = i * (math.pi / 3.0)
            hx = int(cx + math.cos(ang) * (r * 0.55))
            hy = int(cy + math.sin(ang) * (r * 0.55))
            cv2.line(frame, (cx, cy), (hx, hy), color, 1, cv2.LINE_AA)
            cv2.circle(frame, (hx, hy), 3, (255, 255, 255), -1, cv2.LINE_AA)
