from spells.base_spell import BaseSpell


class ShieldSpell(BaseSpell):

    def __init__(self):

        super().__init__(
            name="Shield",
            damage=0,
            mana_cost=10,
            cooldown=3
        )