import logging
from selenium.webdriver.common.by import By

from actions.base import Action
from actions.action_input import ActionInput

class Train(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.go_to("statue")

    def run(self):
        if self.training_availability():
            self.start_training()
            logging.info("Starting knight trening.")

    def training_availability(self):
        els = self.driver.find_elements(By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]')
        availability = len(els) == 1

        return availability

    def start_training(self):
        self.sleep()
        self.driver.find_elements(
            By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]'
        ).click()
        self.sleep()
        self.driver.find_element(
            By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[6]/a[1][text()="Start"]'
        ).click()
