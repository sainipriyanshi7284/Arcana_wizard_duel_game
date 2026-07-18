from spells.base_spell import BaseSpell


class FireSpell(BaseSpell):

    def __init__(self):

        super().__init__(
            name="Fireball",
            damage=30,
            mana_cost=20,
            cooldown=2
        )