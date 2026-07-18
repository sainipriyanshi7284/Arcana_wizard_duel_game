class Player:

    def __init__(self, name, side):
        self.name = name
        self.side = side

        self.hand_landmarks = None
        self.gesture = None

        self.spell = None

        self.health = 100
        self.mana = 100

    def update_hand(self, hand):
        self.hand_landmarks = hand


    def update_gesture(self, gesture):
        self.gesture = gesture

    def update_spell(self, spell):
        self.spell = spell

   
    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def heal(self, amount):
        self.health += amount
        if self.health > 100:
            self.health = 100


    def use_mana(self, amount):
        self.mana -= amount
        if self.mana < 0:
            self.mana = 0

    def restore_mana(self, amount):
        self.mana += amount
        if self.mana > 100:
            self.mana = 100


    def reset(self):

        self.hand_landmarks = None
        self.gesture = None
        self.spell = None

        self.health = 100
        self.mana = 100