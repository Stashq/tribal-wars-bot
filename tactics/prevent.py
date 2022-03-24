from dataclasses import dataclass, fields

from numpy import isin

from data_types import Recruitment


@dataclass
class PreventTactic:
    percentage: int = 10
    wood: Recruitment = Recruitment()
    stone: Recruitment = Recruitment()
    iron: Recruitment = Recruitment()
    wood_and_stone: Recruitment = Recruitment()
    wood_and_iron: Recruitment = Recruitment()
    stone_and_iron: Recruitment = Recruitment()
    wood_and_stone_and_iron: Recruitment = Recruitment()

    def __post_init__(self):
        def get_place(Building_cls, values):
            if values is None:
                return Building_cls()
            else:
                return Building_cls(**values)
        
        if not isinstance(self.percentage, int):
            self.percentage = int(self.percentage)
        
        for field in fields(self):
            if field.name == "percentage":
                continue
            rc = getattr(self, field.name)
            if rc is None:
                setattr(self, field.name, Recruitment())
            if not isinstance(rc, Recruitment):
                setattr(self, field.name, Recruitment(**rc))