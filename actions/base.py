from abc import ABC, abstractmethod
import logging
import numpy as np
from selenium.webdriver.common.by import By
import time

from action_input import ActionInput
from datatypes import Cost


class Action(ABC):
    def __init__(self, input_: ActionInput):
        self.driver = input_.driver
        self.base_url = 'https://pl%d.plemiona.pl/game.php?village=%d' % (input_.world_nr, input_.village)
        self.fundraise = input_.fundraise

    def sleep(mu: float = 1.345, sig: float = 0.35):
        rand = np.random.randn()
        time.sleep(
            abs(rand*sig + mu)
        )

    def go_to(self, screen: str, mode: str = None):
        self.sleep()
        url = self.base_url + '&screen=' + screen
        self.driver.get(url)

        if mode is not None:
            self._go_to_mode(url, mode)

    def _go_to_mode(self, screen_url: str, mode: str):
        self.sleep()
        url = screen_url + '&mode=' + mode
        self.driver.get(url)

        els = self.driver.find_elements(By.XPATH, '//div[@class="content" and text()="Niewłaściwy tryb"]')
        if len(els) > 0:
            msg = 'Invalid mode "%s". Url: %s.' % (mode, url)
            logging.error(msg)
            raise ValueError(msg)

    def get_resources(self, include_fundraise: bool = False) -> Cost:
        '''Returns order: wood, stone, iron'''
        resources = Cost(
            int(self.driver.find_element(By.CSS_SELECTOR, '#wood').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#stone').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#iron').text)
        )

        # substract established fundraise
        if self.fundraise is not None:
            self._substract_fundraise(resources)
        return resources

    def _substract_fundraise(self, resources: Cost) -> Cost:
        if resources.wood - self.fundraise.wood > 0:
            resources.wood -= self.fundraise.wood
        else:
            resources.wood = 0
        if resources.stone - self.fundraise.stone > 0:
            resources.stone -= self.fundraise.stone
        else:
            resources.stone = 0
        if resources.iron - self.fundraise.iron > 0:
            resources.iron -= self.fundraise.iron
        else:
            resources.iron = 0
        return resources

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)
