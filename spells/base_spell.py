class BaseSpell:

    def __init__(self, name, damage, mana_cost, cooldown):

        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.cooldown = cooldown

        self.active = False

    def cast(self):

        self.active = True

    def update(self):
        pass

    def draw(self, frame):
        pass

    def reset(self):

        self.active = False