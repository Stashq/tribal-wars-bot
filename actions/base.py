from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
import numpy as np
import re
from selenium.webdriver.common.by import By
import time
from typing import Union, Type
from furl import furl

from actions.action_input import ActionInput
from data_types import Cost


class Action(ABC):
    def __init__(self, input_: ActionInput):
        self.driver = input_.driver
        self.base_url = 'https://pl%d.plemiona.pl/game.php?village=%d' % (input_.world_nr, input_.village_nr)
        self.fundraise = input_.fundraise
        self.pp_limit = input_.pp_limit

    def sleep(self, mu: float = 1.345, sig: float = 0.35):
        rand = np.random.randn()
        time.sleep(
            abs(rand*sig + mu)
        )

    def go_to(self, screen: str, mode: str = None):
        self.sleep()
        url = self.base_url + '&screen=' + screen
        self.driver.get(url)

        if mode is not None:
            self.change_mode(mode)

    def change_mode(self, mode: str):
        self.sleep()
        url = furl(self.driver.current_url)
        url.args['mode'] = mode
        self.driver.get(url.url)

        els = self.driver.find_elements(By.XPATH, '//div[@class="content" and text()="Niewłaściwy tryb"]')
        if len(els) > 0:
            msg = 'Invalid mode "%s". Url: %s.' % (mode, url)
            logging.error(msg)
            raise ValueError(msg)

    def get_resources(self, deduct_fundraise: bool = True) -> Cost:
        resources = Cost(
            int(self.driver.find_element(By.CSS_SELECTOR, '#wood').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#stone').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#iron').text)
        )
        
        if deduct_fundraise:
            resources = self._substract_fundraise(resources)
        return resources

    def _get_increases(self):
        increases = Cost(
            wood=self._get_resource_increase("wood"),
            stone=self._get_resource_increase("stone"),
            iron=self._get_resource_increase("iron")
        )
        return increases

    def _get_resource_increase(self, resource: str) -> int:
        text = self.driver.find_element(
            By.XPATH, '//*[@id="%s"]' % resource
        ).title
        return int(re.findall(r'\d+', text)[0])


    def _substract_fundraise(self, resources: Cost) -> Cost:
        if resources.wood - self.fundraise["cost"].wood > 0:
            resources.wood -= self.fundraise["cost"].wood
        else:
            resources.wood = 0
        if resources.stone - self.fundraise["cost"].stone > 0:
            resources.stone -= self.fundraise["cost"].stone
        else:
            resources.stone = 0
        if resources.iron - self.fundraise["cost"].iron > 0:
            resources.iron -= self.fundraise["cost"].iron
        else:
            resources.iron = 0
        return resources

    @abstractmethod
    def run(self, *args, **kwargs) -> Union[datetime, timedelta]:
        pass

    def __call__(self, *args, **kwargs) -> Union[datetime, timedelta]:
        return self.run(*args, **kwargs)

    @abstractmethod
    def _get_waiting_time(self) -> timedelta:
        pass

    def _str_to_timedelta(self, delta_str: str, format_: str = "%H:%M:%S") -> timedelta:
        delta = datetime.strptime(delta_str, format_)
        delta = timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
        return delta

    def log_next_attempt_warning(self, cmd: str, td: timedelta) -> timedelta:
        next_attempt = datetime.now() + timedelta(hours=1)
        next_attempt_str = next_attempt.strftime("%Y-%m-%d, %H:%M:%S")
        logging.warning("Cannot %s. Next attempt at %s." % (cmd, next_attempt_str))

    def set_fundraise(self, cost: Cost, action: Type[Action]):
        self.fundraise["cost"].wood = cost.wood
        self.fundraise["cost"].stone = cost.stone
        self.fundraise["cost"].iron = cost.iron
        self.fundraise["action"] = action
        logging.info(
            "Set fundraise: wood %d, stone %d, iron %d." % (cost.wood, cost.stone, cost.iron)
        )

    def _get_storage_size(self) -> int:
        size = self.driver.find_element(
            By.XPATH, '//*[@id="storage"]'
        ).text
        return int(size)

    def _get_pp(self) -> int:
        pp = self.driver.find_element(
            By.XPATH, '//*[@id="premium_points"]'
        ).text
        return int(pp)

    def limit_resources(self, resources: Cost, savings: Cost, limits: Cost):
        wood = self._limit_resource(
            resource=resources.wood, saving=savings.wood,
            fundraise=self.fundraise["cost"].wood, limit=limits.wood)
        stone = self._limit_resource(
            resource=resources.stone, saving=savings.stone,
            fundraise=self.fundraise["cost"].stone, limit=limits.stone)
        iron = self._limit_resource(
            resource=resources.iron, saving=savings.iron,
            fundraise=self.fundraise["cost"].iron, limit=limits.iron)
        return Cost(wood, stone, iron)

    def _limit_resource(self, resource: int, saving: int, fundraise: int, limit: int):
        result = resource
        if saving > fundraise:
            result -= saving
        else:
            result -= fundraise
        
        if result > limit:
            result = limit
        elif result < 0:
            result = 0
        return result
