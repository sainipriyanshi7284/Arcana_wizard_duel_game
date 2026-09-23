# Arcana: Wizard Duel

Welcome to **Arcana: Wizard Duel**, a real-time multiplayer augmented reality (AR) wizard dueling game! Utilizing computer vision and gesture recognition, you and a friend can face off in front of a single webcam, casting spectacular magical spells using real hand gestures. 

The game overlays magical UI elements, stunning procedural particle effects, and dynamic projectiles over your live camera feed, creating a truly immersive wizard dueling experience.

## ✨ Features
- **Real-Time Gesture Recognition**: Uses MediaPipe's advanced hand tracking and gesture recognition models to instantly detect magical hand signs.
- **2-Player Local AR Multiplayer**: Two players stand in front of the camera (Left side = Player 1, Right side = Player 2). The game tracks both players simultaneously.
- **Elemental Spell System**: Five distinct spells to master, each with unique procedural VFX, damage, mana costs, and properties.
- **Projectile Physics & Reflection**: Spells fire across the screen toward the opponent. Defensive shields can reflect enemy projectiles back at them!
- **Immersive Magical UI**: A custom-built UI layer using `Pillow` (PIL) that renders Harry Potter-esque gothic fonts (`OLDENGL.TTF`), ancient parchment spell panels, translucent borders, and ambient floating magic particles.

## 🪄 Spells & Gestures

Master the following gestures to dominate the duel. To cast a spell, perform its gesture to **Charge** it up. Once fully charged, release the gesture to **Cast** the projectile.

| Spell | Element | Gesture | Effect |
|-------|---------|---------|--------|
| **Fireball** | Fire | `Closed_Fist` | Summons a massive, blazing bonfire aura around your hand. Shoots a devastating explosive fireball projectile. |
| **Ice Blast** | Ice | `Victory` (Peace Sign) | Forms crystalline blue procedural ice spikes extending from your fingers. Shoots a barrage of freezing ice shards. |
| **Lightning** | Lightning | `Pointing_Up` | Crackles with procedural purple/magenta lightning arcs around your hand. Fires an erratic electric plasma sphere. |
| **Wind Slash** | Wind | `Thumb_Up` | Conjures swirling teal and white tornados around your wrist. Fires a spinning crescent wind blade. |
| **Shield** | Defense | `Open_Palm` | Generates a massive, stable, concentric magic circle in front of you. **Reflects** incoming enemy projectiles back at the caster! |

## 🛠️ Tech Stack & Architecture

Arcana is built in Python using a modular architecture for high performance and easy expansion.

### Core Libraries
- **OpenCV (`cv2`)**: Powers the main game loop, camera feed processing, image blending, and rapid particle rendering (additive blending/GaussianBlur).
- **MediaPipe (`mediapipe`)**: Handles lightweight, high-performance Hand Tracking and Gesture Recognition using `.task` models.
- **Pillow (`PIL`)**: Manages the high-fidelity UI rendering layer, drawing TrueType Gothic fonts and overlaying weathered parchment textures.
- **NumPy (`numpy`)**: Optimizes mathematical calculations for the ambient particle systems and procedural physics.

### Architecture Overview
- `engine/game.py`: The heart of the game. Manages the main game loop, UI rendering pipeline, projectile state, and collision mechanics.
- `vision/`: Contains `camera.py`, `mediapipe_tracker.py`, and `gesture_recognizer.py` to handle all webcam interfacing and AI inferences.
- `combat/`: Contains `player.py` (managing HP, Mana, and the spell state machine: IDLE -> CHARGING -> CAST) and `spell_projectile.py` for physics.
- `spells/`: Defines the metadata, damage, and cooldowns for the `SpellManager`.
- `effects/`: Contains the massive procedural VFX classes (`fire_vfx.py`, `ice_vfx.py`, `shield_vfx.py`, `lightning_vfx.py`, `wind_vfx.py`). Each class handles the complex math to draw glowing polygons, arcs, and particles on top of the player's hands.

## 🚀 How to Play

1. **Install Dependencies**:
   Ensure you have Python 3.9+ installed.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Game**:
   ```bash
   python main.py
   ```

3. **Duel!**:
   - Player 1 stands on the left side of the camera view, Player 2 on the right.
   - Watch your HP (Red bar) and Mana (Blue bar) at the top of the screen.
   - Form a gesture (e.g., Closed Fist) to begin charging your spell.
   - Once the charging animation completes, drop your hand or switch gestures to fire the projectile at your opponent!
   - Use the `Open_Palm` gesture reactively to block and reflect incoming spells.

## 🎨 Customization
- **UI Textures**: Replace the `parchment_ui_panel_*.jpg` image with your own to change the spell info background.
- **VFX Colors**: You can easily edit the BGR color tuples in the `effects/` classes to change the visual flair of the spells.
