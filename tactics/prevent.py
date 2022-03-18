from dataclasses import dataclass

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