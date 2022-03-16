from datetime import datetime, timedelta
import logging
from selenium.webdriver.common.by import By

from actions.base import Action
from actions.action_input import ActionInput

class Train(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.go_to("statue")

    def run(self) -> timedelta:
        if self._training_availability():
            self._start_training()
        # else:
            # time_delta = datetime.now() + timedelta(hours=1)
            # self.log_next_attempt_warning(
            #     "train knight", timedelta(hours=1))
        time_delta = self._get_waiting_time()
        return time_delta

    def _training_availability(self):
        els = self.driver.find_elements(
            By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]')
        return len(els) == 1

    def _start_training(self):
        self.sleep()
        self.driver.find_element(
            By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]'
        ).click()
        self.sleep()
        try:
            self.driver.find_element(
                By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[6]/a[1][text()="Start"]'
            ).click()
            logging.info("Knight training started.")
        except Exception as e:
            pass

    def _get_waiting_time(self) -> timedelta:
        self.sleep()
        delta_str = self.driver.find_element(
            By.XPATH, '//div[@id="knight_activity"]/span[@data-endtime]'
        ).text

        delta = self._str_to_timedelta(delta_str)
        return delta
