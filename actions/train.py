from datetime import timedelta
import json
import logging
from selenium.webdriver.common.by import By
from typing import Callable

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Cost

class Train(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.in_training_panel = False
        self.path = self.base_path / 'train.json'
        with open(self.path, "r") as file:
            self.settings = json.load(file)
        self.time_after_attempt = timedelta(
            minutes=self.settings["minutes_after_attempt"])

    def run(self) -> timedelta:
        if not self.settings["run"]:
            time_delta = None
        else:
            self.go_to("statue")
            if self._training_availability():
                time_delta = self._run_in_training_panel(
                    self._start_training)
            else:
                time_delta = self._get_waiting_time()
        return time_delta

    def _training_availability(self):
        els = self.driver.find_elements(
            By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]')
        return len(els) == 1

    def _get_training_cost(self):
        resource = self.driver.find_element(
            By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[2]'
        ).text
        resource = int(resource.replace('.', ''))
        return Cost(resource, resource, resource)

    def _run_in_training_panel(self, func: Callable, *args, **kwargs):
        self._go_to_training_panel()
        res = func(*args, **kwargs)
        return res

    def _go_to_training_panel(self):
        self.sleep()
        self.driver.find_element(
            By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]'
        ).click()
        self.in_training_panel = True

    def _enough_resources(self):
        cost = self._get_training_cost()
        resources = self.get_resources()
        resources = self.limit_resources(
            resources, savings=Cost(**self.settings["savings"]), limits=Cost(**self.settings["limits"]))
        return not cost.all_greater(resources)

    def _start_training(self) -> timedelta:
        time_delta = self._get_waiting_time()
        if self._enough_resources():
            self.sleep()
            self.driver.find_element(
                By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[6]/a[1][text()="Start"]'
            ).click()
            self.in_training_panel = False
            logging.info("Knight training started.")
        else:
            time_delta = self.time_after_attempt
            self.set_fundraise(
                cost=self._get_training_cost(),
                action=type(self)
            )
            logging.info("Not enough resources for knight training.")
        return time_delta

    def _get_waiting_time(self) -> timedelta:
        self.sleep()
        if self.in_training_panel:
            delta_str = self.driver.find_element(
                By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[5]'
            ).text
        else:
            delta_str = self.driver.find_element(
                By.XPATH, '//div[@id="knight_activity"]/span[@data-endtime]'
            ).text
        delta = self._str_to_timedelta(delta_str)
        return delta
