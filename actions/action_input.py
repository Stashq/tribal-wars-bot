from dataclasses import dataclass
from selenium.webdriver import WebDriver

from data_types import Cost


@dataclass
class ActionInput:
    driver: WebDriver
    world_nr: int
    village_nr: int
    fundraise: Cost = None
