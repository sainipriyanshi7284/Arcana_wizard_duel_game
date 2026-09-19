import cv2
import numpy as np
import math
import random
from effects.glow import GlowRenderer
from effects.magic_circle import MagicCircleRenderer

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class FantasyHUD:
    """
    Renders the ornate fantasy HUD matching the ARCANA: WIZARD DUEL reference:
    - Gold header crest with "ARCANA" and "WIZARD DUEL" + delicate filigree flourishes
    - Golden glowing center dividing line with 4-pointed star emblems
    - Glowing HP & Mana bars for Player 1 and Player 2
    - Bottom floating spell cards with glowing filigree borders and icons
    - FPS counter and edge vignette
    """

    def __init__(self):
        self._font_cache = {}
        self.time_val = 0.0
        # Ambient background particles for each realm
        self.p1_ambient_embers = [
            {'x': random.uniform(0.04, 0.46), 'y': random.uniform(0.05, 0.98),
             'speed': random.uniform(0.05, 0.16), 'size': random.uniform(2.0, 5.0),
             'seed': random.uniform(0, 100)}
            for _ in range(35)
        ]
        self.p2_ambient_snow = [
            {'x': random.uniform(0.54, 0.96), 'y': random.uniform(0.02, 0.98),
             'speed': random.uniform(0.04, 0.12), 'size': random.uniform(2.0, 5.5),
             'seed': random.uniform(0, 100)}
            for _ in range(38)
        ]

    def draw_elemental_backgrounds(self, frame, dt=0.033):
        """
        Renders rich, cinematic elemental atmospheres for both screens:
        - Left (Player 1): Fiery volcanic sanctuary with molten rim glows, dark ruby vignette, and rising embers
        - Right (Player 2): Glacial frozen citadel with electric cyan aurora rim, sapphire vignette, and drifting frost blizzard
        """
        self.time_val += dt
        h, w = frame.shape[:2]
        cx = w // 2

        # 1. Player 1 (Left Half: 0 to cx) - Fiery Volcanic Realm
        left_overlay = np.zeros((h, cx, 3), dtype=np.uint8)
        # Deep obsidian-crimson background tone
        cv2.rectangle(left_overlay, (0, 0), (cx, h), (18, 10, 38), -1)
        # Warm fiery outer rim & bottom molten glow
        cv2.ellipse(left_overlay, (0, h // 2), (int(cx * 0.8), int(h * 0.7)), 0, 0, 360, (10, 45, 140), -1)
        cv2.ellipse(left_overlay, (cx // 2, h), (int(cx * 0.6), int(h * 0.3)), 0, 0, 360, (0, 70, 210), -1)
        left_overlay = cv2.GaussianBlur(left_overlay, (65, 65), 0)
        roi_p1 = frame[0:h, 0:cx]
        cv2.addWeighted(roi_p1, 0.78, left_overlay, 0.22, 0, dst=roi_p1)

        # Faint arcane fire circle watermark in background
        bg_ang = self.time_val * 0.4
        MagicCircleRenderer.draw_arcane_ring(frame, cx // 2, h // 2, radius=int(min(cx, h) * 0.38),
                                            angle=bg_ang, color=(10, 50, 140), num_glyphs=8)

        # 2. Player 2 (Right Half: cx to w) - Glacial Frozen Realm
        right_overlay = np.zeros((h, w - cx, 3), dtype=np.uint8)
        # Deep obsidian-sapphire background tone
        cv2.rectangle(right_overlay, (0, 0), (w - cx, h), (38, 16, 12), -1)
        # Cool electric cyan outer rim & top aurora glow
        cv2.ellipse(right_overlay, (w - cx, h // 2), (int((w - cx) * 0.8), int(h * 0.7)), 0, 0, 360, (140, 85, 15), -1)
        cv2.ellipse(right_overlay, ((w - cx) // 2, 0), (int((w - cx) * 0.6), int(h * 0.3)), 0, 0, 360, (210, 130, 20), -1)
        right_overlay = cv2.GaussianBlur(right_overlay, (65, 65), 0)
        roi_p2 = frame[0:h, cx:w]
        cv2.addWeighted(roi_p2, 0.78, right_overlay, 0.22, 0, dst=roi_p2)

        # Faint arcane frost circle watermark in background
        MagicCircleRenderer.draw_arcane_ring(frame, cx + (w - cx) // 2, h // 2, radius=int(min(w - cx, h) * 0.38),
                                            angle=-bg_ang, color=(140, 90, 20), num_glyphs=8)

        # 3. High-Intensity Ambient Drifting Embers (Player 1 Side)
        for emb in self.p1_ambient_embers:
            emb['y'] -= emb['speed'] * dt
            if emb['y'] < 0.04:
                emb['y'] = 0.98
                emb['x'] = random.uniform(0.04, 0.46)

            px = int((emb['x'] + math.sin(self.time_val * 4.5 + emb['seed']) * 0.025) * w)
            py = int(emb['y'] * h)
            size = max(1, int(emb['size']))

            # Glowing ember halo
            glow = GlowRenderer.get_radial_glow(int(size * 3.5), (0, 120, 255), center_intensity=0.8)
            GlowRenderer.draw_additive(frame, glow, px, py)
            cv2.circle(frame, (px, py), size, (10, 160, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), max(1, size - 2), (200, 245, 255), -1, cv2.LINE_AA)

        # 4. High-Intensity Ambient Drifting Snowflakes & Frost Crystals (Player 2 Side)
        for snw in self.p2_ambient_snow:
            snw['y'] += snw['speed'] * dt
            if snw['y'] > 0.98:
                snw['y'] = 0.04
                snw['x'] = random.uniform(0.54, 0.96)

            px = int((snw['x'] + math.sin(self.time_val * 3.5 + snw['seed']) * 0.025) * w)
            py = int(snw['y'] * h)
            size = max(1, int(snw['size']))

            # Glowing frost halo
            glow = GlowRenderer.get_radial_glow(int(size * 3.5), (255, 210, 60), center_intensity=0.75)
            GlowRenderer.draw_additive(frame, glow, px, py)
            cv2.circle(frame, (px, py), size, (255, 230, 120), -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), max(1, size - 2), (255, 255, 255), -1, cv2.LINE_AA)


    def _get_font(self, size, bold=False):
        if not HAS_PIL:
            return None
        key = (size, bold)
        if key in self._font_cache:
            return self._font_cache[key]

        font_names = [
            "georgia.ttf", "times.ttf", "palatino.ttf", "arial.ttf", "segoeui.ttf"
        ]
        font = None
        for fn in font_names:
            try:
                font = ImageFont.truetype(fn, size)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        self._font_cache[key] = font
        return font

    def draw_text_pil(self, frame, text, pos, font_size, color=(255, 255, 255), bold=False, center=False):
        """
        Renders crisp anti-aliased text onto the OpenCV frame using PIL.
        pos: (x, y)
        color: (B, G, R)
        """
        if not HAS_PIL:
            cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_COMPLEX, font_size / 30.0, color, 1, cv2.LINE_AA)
            return

        font = self._get_font(font_size, bold)
        x, y = pos

        # Calculate bounding box using PIL
        dummy_img = Image.new('RGB', (1, 1))
        draw_dummy = ImageDraw.Draw(dummy_img)
        bbox = draw_dummy.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if center:
            x = x - text_w // 2

        fh, fw = frame.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(fw, x + text_w + 15)
        y2 = min(fh, y + text_h + 15)

        if x1 >= x2 or y1 >= y2:
            return

        roi = frame[y1:y2, x1:x2]
        rgb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_roi)
        draw = ImageDraw.Draw(pil_img)

        # Draw text in RGB
        draw.text((x - x1, y - y1), text, font=font, fill=(color[2], color[1], color[0]))

        bgr_res = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        frame[y1:y2, x1:x2] = bgr_res

    def draw_filigree_scroll(self, frame, cx, cy, flip=False, color=(100, 180, 240)):
        """
        Draws ornate fantasy filigree flourishes flanking the title.
        """
        direction = -1 if flip else 1
        steps = 35
        pts_main = []
        pts_sub = []

        for i in range(steps):
            t = i / float(steps - 1)
            # Upper arching scroll curve
            dx = direction * (t * 140 + math.sin(t * math.pi) * 15)
            dy = -math.sin(t * math.pi * 0.9) * 22 + (t * 12)
            pts_main.append([int(cx + dx), int(cy + dy)])

            # Lower subtle curl
            if t < 0.7:
                dx2 = direction * (t * 100)
                dy2 = math.sin(t * math.pi * 1.2) * 10 + (t * 5)
                pts_sub.append([int(cx + dx2), int(cy + dy2)])

        cv2.polylines(frame, [np.array(pts_main, dtype=np.int32)], False, color, 1, cv2.LINE_AA)
        if pts_sub:
            cv2.polylines(frame, [np.array(pts_sub, dtype=np.int32)], False, color, 1, cv2.LINE_AA)

        # End scroll loop & diamond accent
        end_pt = pts_main[-1]
        cv2.circle(frame, (end_pt[0], end_pt[1]), 3, color, 1, cv2.LINE_AA)
        cv2.circle(frame, (end_pt[0], end_pt[1]), 1, (220, 245, 255), -1, cv2.LINE_AA)

        # Small diamond flourish at top peak
        peak_idx = int(steps * 0.45)
        peak_pt = pts_main[peak_idx]
        MagicCircleRenderer.draw_ornate_star_emblem(frame, peak_pt[0], peak_pt[1] - 3, size=4,
                                                   color=color, glow_color=(40, 120, 220))

    def draw_header(self, frame):
        """
        Draws the ornate top header:
        "ARCANA"
        "◆ WIZARD DUEL ◆"
        with gleaming golden filigree flourishes.
        """
        h, w = frame.shape[:2]
        cx = w // 2

        # Glowing filigree scrolls flanking "ARCANA"
        self.draw_filigree_scroll(frame, cx - 90, 34, flip=True, color=(110, 195, 255))
        self.draw_filigree_scroll(frame, cx + 90, 34, flip=False, color=(110, 195, 255))

        # Soft glow behind "ARCANA"
        title_glow = GlowRenderer.get_radial_glow(45, (60, 160, 255), center_intensity=0.8)
        GlowRenderer.draw_additive(frame, title_glow, cx, 22)

        # "ARCANA" title in glowing solar gold
        self.draw_text_pil(frame, "ARCANA", (cx, 4), font_size=30, color=(130, 225, 255), bold=True, center=True)

        # "WIZARD DUEL" subtitle flanked by procedural golden star emblems
        self.draw_text_pil(frame, "WIZARD DUEL", (cx, 40), font_size=13, color=(180, 220, 255), bold=True, center=True)
        MagicCircleRenderer.draw_ornate_star_emblem(frame, cx - 62, 47, size=4, color=(140, 220, 255), glow_color=(60, 150, 255))
        MagicCircleRenderer.draw_ornate_star_emblem(frame, cx + 62, 47, size=4, color=(140, 220, 255), glow_color=(60, 150, 255))

    def draw_center_divider(self, frame):
        """
        Draws the vertical glowing divider line with ornate 4-pointed star emblems and rotating center ring.
        """
        h, w = frame.shape[:2]
        cx = w // 2

        # Glowing vertical line (dual-layer beam)
        GlowRenderer.draw_glowing_line(
            frame,
            (cx, 58),
            (cx, h - 22),
            color=(210, 240, 255),
            thickness=2,
            glow_color=(70, 160, 255),
            glow_thickness=7
        )
        cv2.line(frame, (cx, 58), (cx, h - 22), (255, 255, 255), 1, cv2.LINE_AA)

        # Three ornate star emblems: Top, Middle, Bottom
        top_y = 65
        mid_y = h // 2
        bot_y = h - 25

        MagicCircleRenderer.draw_ornate_star_emblem(frame, cx, top_y, size=12,
                                                   color=(130, 215, 255), glow_color=(60, 150, 255))
        # Center star with rotating micro arcane ring
        MagicCircleRenderer.draw_arcane_ring(frame, cx, mid_y, radius=24,
                                            angle=self.time_val * 1.5, color=(140, 215, 255), num_glyphs=6)
        MagicCircleRenderer.draw_ornate_star_emblem(frame, cx, mid_y, size=16,
                                                   color=(140, 225, 255), glow_color=(70, 160, 255))
        MagicCircleRenderer.draw_ornate_star_emblem(frame, cx, bot_y, size=12,
                                                   color=(130, 215, 255), glow_color=(60, 150, 255))

    def draw_stat_bar(self, frame, x, y, width, height, current_val, max_val, bar_type="HP"):
        """
        Draws an ornate glowing status bar with intense gradient fill and metallic gold frame.
        """
        ratio = max(0.0, min(1.0, current_val / float(max_val)))
        fill_w = int(width * ratio)

        # Dark transparent background slot
        cv2.rectangle(frame, (x, y), (x + width, y + height), (18, 15, 24), -1)

        if fill_w > 0:
            if bar_type == "HP":
                # High-Intensity Molten Ruby
                fill_color = (25, 25, 250)
                glow_color = (15, 30, 230)
                highlight_color = (160, 180, 255)
            else:
                # High-Intensity Electric Cyan/Azure
                fill_color = (255, 175, 20)
                glow_color = (230, 120, 10)
                highlight_color = (255, 245, 190)

            # Filled portion
            cv2.rectangle(frame, (x + 1, y + 1), (x + fill_w - 1, y + height - 1), fill_color, -1)

            # Incandescent top highlight line
            cv2.line(frame, (x + 2, y + 2), (x + fill_w - 2, y + 2), highlight_color, 1, cv2.LINE_AA)

            # Ambient bar glow
            glow = GlowRenderer.get_radial_glow(int(height * 2.0), glow_color, center_intensity=0.75)
            GlowRenderer.draw_additive(frame, glow, x + fill_w // 2, y + height // 2)

        # Ornate metallic frame with gold corners
        cv2.rectangle(frame, (x, y), (x + width, y + height), (120, 140, 170), 1)
        cv2.rectangle(frame, (x - 1, y - 1), (x + width + 1, y + height + 1), (60, 70, 90), 1)
        # Gold corner rivets
        for cx_r, cy_r in [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]:
            cv2.circle(frame, (cx_r, cy_r), 2, (120, 210, 255), -1, cv2.LINE_AA)

    def draw_player_hud(self, frame, player1, player2):
        """
        Draws Player 1 and Player 2 stats (HP, Mana, and labels) matching the reference.
        """
        h, w = frame.shape[:2]

        # --- Player 1 (Left) ---
        p1_x = 35
        bar_w = 190
        bar_h = 14

        # "Player 1" title with subtle warm glow
        self.draw_text_pil(frame, "Player 1", (p1_x, 16), font_size=21, color=(255, 235, 220), bold=True)

        # HP Bar & Text
        self.draw_stat_bar(frame, p1_x, 46, bar_w, bar_h, player1.health, 100, "HP")
        self.draw_text_pil(frame, f"HP: {int(player1.health)}", (p1_x + bar_w + 14, 43), font_size=13, color=(255, 220, 220), bold=True)

        # Mana Bar & Text
        self.draw_stat_bar(frame, p1_x, 68, bar_w, bar_h, player1.mana, 100, "MANA")
        self.draw_text_pil(frame, f"Mana: {int(player1.mana)}", (p1_x + bar_w + 14, 65), font_size=13, color=(210, 235, 255), bold=True)

        # --- Player 2 (Right) ---
        p2_bar_x = w - 35 - bar_w

        # "Player 2" title with subtle cool glow
        self.draw_text_pil(frame, "Player 2", (w - 120, 16), font_size=21, color=(220, 240, 255), bold=True)

        # HP Bar & Text (text on left of bar)
        self.draw_text_pil(frame, f"HP: {int(player2.health)}", (p2_bar_x - 72, 43), font_size=13, color=(255, 220, 220), bold=True)
        self.draw_stat_bar(frame, p2_bar_x, 46, bar_w, bar_h, player2.health, 100, "HP")

        # Mana Bar & Text (text on left of bar)
        self.draw_text_pil(frame, f"Mana: {int(player2.mana)}", (p2_bar_x - 88, 65), font_size=13, color=(210, 235, 255), bold=True)
        self.draw_stat_bar(frame, p2_bar_x, 68, bar_w, bar_h, player2.mana, 100, "MANA")

    def _draw_flame_icon(self, frame, cx, cy, size=20):
        """
        Draws a stylized bright orange/yellow flame icon.
        """
        pts = np.array([
            [cx, cy - size],
            [cx + int(size * 0.45), cy - int(size * 0.2)],
            [cx + int(size * 0.65), cy + int(size * 0.35)],
            [cx + int(size * 0.4), cy + size],
            [cx, cy + int(size * 0.85)],
            [cx - int(size * 0.4), cy + size],
            [cx - int(size * 0.65), cy + int(size * 0.35)],
            [cx - int(size * 0.45), cy - int(size * 0.2)],
        ], dtype=np.int32)
        cv2.fillPoly(frame, [pts], (15, 110, 255), lineType=cv2.LINE_AA)

        # Inner yellow core
        s2 = int(size * 0.55)
        pts_in = np.array([
            [cx, cy - s2 + 3],
            [cx + int(s2 * 0.5), cy + int(s2 * 0.4)],
            [cx, cy + s2],
            [cx - int(s2 * 0.5), cy + int(s2 * 0.4)],
        ], dtype=np.int32)
        cv2.fillPoly(frame, [pts_in], (60, 235, 255), lineType=cv2.LINE_AA)

        glow = GlowRenderer.get_radial_glow(int(size * 1.6), (20, 140, 255), center_intensity=0.85)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

    def _draw_snowflake_icon(self, frame, cx, cy, size=20):
        """
        Draws a stylized icy snowflake icon.
        """
        s = size
        color = (255, 240, 150)
        for i in range(6):
            ang = i * (math.pi / 3.0)
            ex = int(cx + math.cos(ang) * s)
            ey = int(cy + math.sin(ang) * s)
            cv2.line(frame, (cx, cy), (ex, ey), color, 2, cv2.LINE_AA)

            bx = cx + math.cos(ang) * (s * 0.6)
            by = cy + math.sin(ang) * (s * 0.6)
            for bo in [-0.7, 0.7]:
                ba = ang + bo
                cv2.line(frame, (int(bx), int(by)),
                         (int(bx + math.cos(ba) * (s * 0.38)), int(by + math.sin(ba) * (s * 0.38))),
                         color, 1, cv2.LINE_AA)

        cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)
        glow = GlowRenderer.get_radial_glow(int(size * 1.6), (255, 210, 70), center_intensity=0.85)
        GlowRenderer.draw_additive(frame, glow, cx, cy)

    def _draw_shield_icon(self, frame, cx, cy, size=20):
        s = size
        pts = np.array([
            [cx, cy - s],
            [cx + s, cy - int(s * 0.6)],
            [cx + int(s * 0.7), cy + int(s * 0.4)],
            [cx, cy + s],
            [cx - int(s * 0.7), cy + int(s * 0.4)],
            [cx - s, cy - int(s * 0.6)],
        ], dtype=np.int32)
        cv2.polylines(frame, [pts], True, (100, 230, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)

    def _draw_lightning_icon(self, frame, cx, cy, size=20):
        s = size
        pts = np.array([
            [cx + 2, cy - s],
            [cx - int(s * 0.6), cy + 1],
            [cx, cy + 1],
            [cx - 2, cy + s],
            [cx + int(s * 0.6), cy - 1],
            [cx, cy - 1],
        ], dtype=np.int32)
        cv2.fillPoly(frame, [pts], (255, 240, 100), lineType=cv2.LINE_AA)

    def _draw_wind_icon(self, frame, cx, cy, size=20):
        s = size
        cv2.ellipse(frame, (cx, cy), (s, int(s * 0.5)), 15, 0, 280, (180, 255, 180), 2, cv2.LINE_AA)
        cv2.ellipse(frame, (cx + 2, cy + 4), (int(s * 0.6), int(s * 0.3)), -10, 30, 310, (220, 255, 220), 1, cv2.LINE_AA)

    def draw_spell_card(self, frame, center_x, bottom_y, spell_name, gesture_name, theme="fire"):
        """
        Draws the ornate floating spell badge at the bottom with intense elemental glowing borders.
        """
        card_w = 280
        card_h = 72
        x1 = center_x - card_w // 2
        y1 = bottom_y - card_h
        x2 = x1 + card_w
        y2 = bottom_y

        fh, fw = frame.shape[:2]
        if x1 < 0 or y1 < 0 or x2 >= fw or y2 >= fh:
            return

        # 1. Dark translucent card background with subtle theme tint
        roi = frame[y1:y2, x1:x2]
        dark_card = np.zeros_like(roi)
        if theme == "fire":
            dark_card[:] = (20, 12, 35)
        elif theme == "ice":
            dark_card[:] = (35, 18, 15)
        else:
            dark_card[:] = (20, 18, 30)
        cv2.addWeighted(roi, 0.22, dark_card, 0.78, 0, dst=roi)

        # 2. Ornate filigree border colors
        if theme == "fire":
            outer_color = (0, 145, 255)
            inner_color = (25, 225, 255)
            glow_color = (0, 80, 220)
        elif theme == "ice":
            outer_color = (255, 220, 25)
            inner_color = (255, 160, 0)
            glow_color = (220, 110, 10)
        elif theme == "shield":
            outer_color = (120, 230, 255)
            inner_color = (80, 180, 240)
            glow_color = (60, 140, 210)
        elif theme == "lightning":
            outer_color = (255, 230, 130)
            inner_color = (220, 190, 80)
            glow_color = (200, 150, 60)
        else:
            outer_color = (160, 245, 180)
            inner_color = (100, 215, 130)
            glow_color = (80, 170, 100)

        # Ambient card edge glow
        card_glow = GlowRenderer.get_radial_glow(int(card_h * 1.3), glow_color, center_intensity=0.6)
        GlowRenderer.draw_additive(frame, card_glow, center_x, y1 + card_h // 2)

        # Card double border
        cv2.rectangle(frame, (x1, y1), (x2, y2), outer_color, 2, cv2.LINE_AA)
        cv2.rectangle(frame, (x1 + 3, y1 + 3), (x2 - 3, y2 - 3), inner_color, 1, cv2.LINE_AA)

        # Corner ornate diamond stars
        for bx, by in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            MagicCircleRenderer.draw_ornate_star_emblem(frame, bx, by, size=6,
                                                       color=inner_color, glow_color=glow_color)

        # 3. Spell Icon
        icon_cx = x1 + 46
        icon_cy = y1 + card_h // 2
        if theme == "fire":
            self._draw_flame_icon(frame, icon_cx, icon_cy, size=21)
        elif theme == "ice":
            self._draw_snowflake_icon(frame, icon_cx, icon_cy, size=20)
        elif theme == "shield":
            self._draw_shield_icon(frame, icon_cx, icon_cy, size=20)
        elif theme == "lightning":
            self._draw_lightning_icon(frame, icon_cx, icon_cy, size=20)
        else:
            self._draw_wind_icon(frame, icon_cx, icon_cy, size=20)

        # 4. Spell Title & Gesture Text
        title_text = f"{spell_name} Spell" if "Spell" not in spell_name else spell_name
        gesture_text = f"({gesture_name.replace('_', ' ')})"
        self.draw_text_pil(frame, title_text, (x1 + 88, y1 + 14), font_size=19, color=(255, 255, 255), bold=True)
        self.draw_text_pil(frame, gesture_text, (x1 + 90, y1 + 40), font_size=13, color=(220, 230, 245))

    def draw_fps(self, frame, delta_time):
        fps = int(1.0 / delta_time) if delta_time > 0 else 0
        self.draw_text_pil(frame, f"FPS: {fps}", (24, frame.shape[0] - 25), font_size=14, color=(230, 230, 240))

    def draw_vignette(self, frame):
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (25, 20, 35), 2)
        s = 18
        for x, y, dx, dy in [(0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)]:
            cv2.line(frame, (x, y), (x + dx * s, y), (100, 180, 240), 2, cv2.LINE_AA)
            cv2.line(frame, (x, y), (x, y + dy * s), (100, 180, 240), 2, cv2.LINE_AA)
            cv2.line(frame, (x + dx * 4, y + dy * 4), (x + dx * (s - 4), y + dy * 4), (60, 120, 180), 1, cv2.LINE_AA)
            cv2.line(frame, (x + dx * 4, y + dy * 4), (x + dx * 4, y + dy * (s - 4)), (60, 120, 180), 1, cv2.LINE_AA)
