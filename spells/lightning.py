from spells.base_spell import BaseSpell


class LightningSpell(BaseSpell):

    def __init__(self):

        super().__init__(
            name="Lightning",
            damage=40,
            mana_cost=30,
            cooldown=4
        )