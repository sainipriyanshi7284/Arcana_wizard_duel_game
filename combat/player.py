class Player:

    def __init__(self, name, side):
        self.name = name
        self.side = side

        self.spell_state = "IDLE"
        self.charge_time = 0.0
        self.locked_spell = None
        self.locked_gesture = "None"
        self.ui_message = ""
        self.message_timer = 0.0
        self.last_cast_damage = 0

        self.health = 100
        self.mana = 100
        self.is_defeated = False

    def update_hand(self, hand):
        self.hand_landmarks = hand

    def game_over(self):
        return self.is_defeated

    def update_spell_state(self, dt, current_gesture, target_player, spell_manager):
        if self.is_defeated:
            return


        if self.spell_state == "IDLE":
            if current_gesture != "None" and current_gesture != "":
                spell = spell_manager.get_spell(current_gesture)
                if spell:
                    self.locked_spell = spell
                    self.locked_gesture = current_gesture
                    self.spell_state = "CHARGING"
                    self.charge_time = 0.0
                    self.ui_message = ""

        elif self.spell_state == "CHARGING":
            self.charge_time += dt
            
            # Check for auto-cast at 5 seconds
            if self.charge_time >= 5.0:
                self.charge_time = 5.0
                self._attempt_cast(target_player)
                
            # Check for gesture change (early release)
            elif current_gesture != self.locked_gesture:
                if self.charge_time < 1.0:
                    self.spell_state = "CANCELLED"
                    self.ui_message = f"{self.locked_spell.name} CANCELLED"
                    self.message_timer = 1.5
                else:
                    self._attempt_cast(target_player)

        elif self.spell_state in ["CAST", "CANCELLED", "NEEDS_RESET"]:
            self.message_timer -= dt
            
            # Immediately allow casting a new spell if they change to a new valid gesture
            if current_gesture != "None" and current_gesture != "" and current_gesture != self.locked_gesture:
                spell = spell_manager.get_spell(current_gesture)
                if spell:
                    self.locked_spell = spell
                    self.locked_gesture = current_gesture
                    self.spell_state = "CHARGING"
                    self.charge_time = 0.0
                    self.ui_message = ""
                    return
            
            # Standard timeout fallback
            if self.message_timer <= 0 and self.spell_state in ["CAST", "CANCELLED"]:
                self.spell_state = "NEEDS_RESET"
                
            if self.spell_state == "NEEDS_RESET":
                # Wait for them to release the previous gesture to prevent repeated casting
                if current_gesture != self.locked_gesture:
                    self.spell_state = "IDLE"
                    self.locked_spell = None
                    self.locked_gesture = "None"

    def _attempt_cast(self, target_player):
        # Calculate scaled damage
        charge_ratio = self.charge_time / 5.0
        final_damage = int(self.locked_spell.damage * charge_ratio)
        
        # Check Mana
        if self.mana >= self.locked_spell.mana_cost:
            self.use_mana(self.locked_spell.mana_cost)
            self.last_cast_damage = final_damage
            
            self.last_cast_damage = final_damage
            self.spell_state = "CAST"
            self.ui_message = f"{self.locked_spell.name} CAST!\nDamage: {final_damage}\nMana: -{self.locked_spell.mana_cost}"
            self.message_timer = 2.0
        else:
            self.spell_state = "CANCELLED"
            self.ui_message = f"NO MANA for {self.locked_spell.name}!"
            self.message_timer = 1.5

   
    def take_damage(self, damage):
        if not self.is_defeated:
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.is_defeated = True

    def heal(self, amount):
        if not self.is_defeated:
            self.health += amount
            if self.health > 100:
                self.health = 100


    def reset(self):
        self.hand_landmarks = None
        self.spell_state = "IDLE"
        self.charge_time = 0.0
        self.locked_spell = None
        self.locked_gesture = "None"
        self.ui_message = ""
        self.message_timer = 0.0
        
        self.health = 100
        self.mana = 100
        self.is_defeated = False


    def use_mana(self, amount):
        if self.mana >= amount and not self.is_defeated:
            self.mana -= amount
            return True
        return False

    def restore_mana(self, amount):
        if not self.is_defeated:
            self.mana += amount
            if self.mana > 100:
                self.mana = 100