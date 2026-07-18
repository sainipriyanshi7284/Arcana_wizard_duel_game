from spells.base_spell import BaseSpell


class WindSpell(BaseSpell):

    def __init__(self):

        super().__init__(
            name="Wind Slash",
            damage=25,
            mana_cost=18,
            cooldown=2
        )