import csv
from datetime import datetime, timedelta
import logging
from pathlib import Path
import re
from selenium.webdriver.common.by import By

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Cost


class Build(Action):
    def __init__(self, input_: ActionInput, path: Path = Path("data/build.csv")):
        super().__init__(input_)
        self.path = path
        with open(path, "r") as file:
            commissions = list(csv.reader(file))
        self.commissions = commissions

    def commission_building(self, building: str):
        self.sleep()
        self.driver.find_element(
            By.XPATH,
            '//a[contains(text(), "Poziom") and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
        ).click()

        with open(self.path, "w") as file:
            csv.writer(file).writerows(
                self.commissions[1:])

    def _can_build(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//a[contains(text(), "Poziom") and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
        )
        return len(els) > 0

    def _full_queue(self, building: str):
        full_queue_elements = self.driver.find_elements(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[7]/span[text()="Kolejka jest obecnie pełna"]' % building
        )
        return len(full_queue_elements) > 0

    def _lack_of_resources(self, building: str):
        lack_of_resources_elements = self.driver.find_elements(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Surowce dostępne")]' % building
        )
        return len(lack_of_resources_elements) > 0

    def _assert_build(self, building: str):
        if self._can_build(building):
            return True
        elif self._full_queue(building):
            return False
        elif self._lack_of_resources(building):
            return False
        else:
            raise ValueError("Unknown building limitation.")

    def _get_waiting_time(self, building: str) -> timedelta:
        if self._can_build(building):
            delta = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[5]' % building
            ).text
            waiting_time = self._str_to_timedelta(delta)
        elif self._full_queue(building):
            delta = self.driver.find_element(
                By.XPATH,
                '//*[@id="buildqueue"]/tr[2]/td[2]/span[@data-endtime]'
            ).text
            waiting_time = self._str_to_timedelta(delta)
        elif self._lack_of_resources(building):
            text = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Surowce dostępne")]' % building
            ).text
            waiting_time = datetime.now()
            if len(re.findall('dzisiaj', text)) > 0:
                pass
            elif len(re.findall('jutro', text)) > 0:
                waiting_time.day += timedelta(days=1)
            elif len(re.findall('\d\d:\d\d:\d\d'), text) > 0:
                delta = self._str_to_timedelta(text[-8:])
                waiting_time += delta
            else:
                print("!!! Unknown text: %s" % text)
            waiting_time = waiting_time.replace(hour=int(text[-5:-3]))
            waiting_time = waiting_time.replace(minute=int(text[-2:]))
        return waiting_time

    def run(self):
        if len(self.commissions) == 0:
            return None
        self.go_to(screen="main")

        building, fundraise = self.commissions[0]

        can_run = self._assert_build(building)
        waiting_time = self._get_waiting_time(building)

        if can_run:
            self.commission_building(building)
        elif fundraise == '1':
            self.set_fundraise(
                self._get_building_cost(building), type(self)
            )

        return waiting_time

    def _get_building_cost(self, building: str):
        wood = self.driver.find_element(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[2]' % building
        ).text
        stone = self.driver.find_element(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[3]' % building
        ).text
        iron = self.driver.find_element(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[4]' % building
        ).text
        return Cost(int(wood), int(stone), int(iron))
