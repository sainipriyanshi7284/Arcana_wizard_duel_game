from spells.base_spell import BaseSpell


class IceSpell(BaseSpell):

    def __init__(self):

        super().__init__(
            name="Ice Blast",
            damage=20,
            mana_cost=15,
            cooldown=2
        )