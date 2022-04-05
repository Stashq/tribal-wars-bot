from dataclasses import dataclass, field
from selenium.webdriver import Chrome
from typing import Dict

from data_types import Cost


@dataclass
class ActionInput:
    driver: Chrome
    current_village_url: str
    village_coordinates: str
    fundraise: Dict = field(
        default_factory=lambda: {"cost": Cost(), "action": None})
    pp_limit: int = 9999999
