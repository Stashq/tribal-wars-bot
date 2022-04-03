from dataclasses import dataclass, field
from selenium.webdriver import Chrome
from typing import Dict

from data_types import Cost


@dataclass
class ActionInput:
    driver: Chrome
    world_nr: int
    village_nr: int
    fundraise: Dict = field(
        default_factory=lambda: {"cost": Cost(), "action": None})
    pp_limit: int = 9999999
