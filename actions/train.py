from datetime import datetime, timedelta
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
        self.time_after_attempt = timedelta(minutes=15)

    def run(self) -> timedelta:
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
        wood = self.driver.find_element(
            By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[2]'
        ).text
        stone = self.driver.find_element(
            By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[3]'
        ).text
        iron = self.driver.find_element(
            By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[4]'
        ).text
        return Cost(
            int(wood), int(stone), int(iron))

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
        return cost.all_less(resources)

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
