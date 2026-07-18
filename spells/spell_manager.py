from spells.fire import FireSpell
from spells.ice import IceSpell
from spells.lightning import LightningSpell
from spells.shield import ShieldSpell
from spells.wind import WindSpell


class SpellManager:

    def __init__(self):

        self.spells = {

            "Closed_Fist": FireSpell(),

            "Victory": IceSpell(),

            "Open_Palm": ShieldSpell(),

            "Pointing_Up": LightningSpell(),

            "Thumb_Up": WindSpell(),

        }

    def get_spell(self, gesture):

        return self.spells.get(gesture, None)