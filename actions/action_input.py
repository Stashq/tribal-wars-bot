from dataclasses import dataclass, field
from datetime import timedelta
from selenium.webdriver import Chrome
from typing import Dict

from data_types import Cost


@dataclass
class ActionInput:
    driver: Chrome
    current_village_url: str
    village_coordinates: str
    next_attempt: timedelta = timedelta(hours=2)
    fundraise: Dict = field(
        default_factory=lambda: {"cost": Cost(), "action": None})
    pp_limit: int = 9999999
