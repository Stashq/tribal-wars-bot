from dataclasses import dataclass
from selenium.webdriver import Chrome
from typing import Type

from data_types import Cost


@dataclass
class ActionInput:
    driver: Chrome
    world_nr: int
    village_nr: int
    fundraise: Cost = None
    fundraise_action: Type = None
