import csv
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import re
from selenium.webdriver.common.by import By
from typing import Literal, Union, Tuple

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
            '//a[(contains(text(), "Poziom") or contains(text(), "Wybuduj")) '\
            'and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
        ).click()
        self._remove_first_commission()

    def _remove_first_commission(self) -> Tuple[str, int]:
        building, fundraise = self.commissions.pop(0)
        with open(self.path, "w") as file:
            csv.writer(file).writerows(
                self.commissions)
        return building, fundraise

    def _can_build(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//a[(contains(text(), "Poziom") or contains(text(), "Wybuduj")) '\
            'and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
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

    def _unmet_requirements(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//*[@id="buildings_unmet"]/tbody//a[contains(@href, "%s")]' % building)
        return len(els) > 0

    def _unknown_building(self, building: str):
        res = building not in [
            "main", "barracks", "stable", "garage", "smith", "statue", "market",
            "wood", "stone", "iron", "farm", "storage", "hide", "wall", "snob"
        ]
        return res

    def _raise_unknown_limitation_error(self, building: str):
        text = "Unknown building limitation for building %s. " % building
        els = self.driver.find_elements(
            By.XPATH, '//*[@id="main_buildrow_%s"]/td[7]/span' % building)
        if len(els) > 0:
            text += 'Cell text: %s.' % els[0].text
        raise ValueError(text)
             
    def _assert_build(self, building: str):
        if self._can_build(building):
            return True
        elif self._full_queue(building):
            return False
        elif self._lack_of_resources(building):
            return False
        elif self._unmet_requirements(building):
            return False
        elif self._unknown_building(building):
            return False
        else:
            self._raise_unknown_limitation_error(building)

    def _get_waiting_time(self, building: str) -> timedelta:
        if self._can_build(building):
            delta = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[5]' % building
            ).text
            waiting_time = self._str_to_timedelta(delta)
        elif self._full_queue(building) or self._unmet_requirements(building):
            els = self.driver.find_elements(
                By.XPATH,
                '//*[@id="buildqueue"]/tr[2]/td[2]/span[@data-endtime]'
            )
            if len(els) > 0:
                delta = els[0].text
                waiting_time = self._str_to_timedelta(delta)
            else:
                waiting_time = None
        elif self._lack_of_resources(building):
            text = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Surowce dostępne")]' % building
            ).text
            if len(re.findall('dzisiaj', text)) > 0:
                waiting_time = datetime.now()
            elif len(re.findall('jutro', text)) > 0:
                waiting_time = datetime.now() + timedelta(days=1)
            elif len(re.findall('\d\d:\d\d:\d\d'), text) > 0:
                delta = self._str_to_timedelta(text[-8:])
                waiting_time = datetime.now() + delta
            else:
                raise ValueError("!!! Unknown text: %s" % text)
            waiting_time = waiting_time.replace(hour=int(text[-5:-3]))
            waiting_time = waiting_time.replace(minute=int(text[-2:]))
        else:
            raise ValueError("Unknown condition for building %s." % building)
        return waiting_time

    def _requirements_over_90_percents(self, building: str):
        cost = self._get_building_cost(building)
        size = self._get_storage_size()
        max_perc = max([
            cost.wood/size, cost.stone/size, cost.iron/size])
        return max_perc > 0.9

    def _add_commission(self, building: str, fundraise: Union[str, int, bool] = "1"):
        self.commissions = [[building, fundraise]] + self.commissions
        with open(self.path, "w") as file:
            csv.writer(file).writerows(
                self.commissions)

    def _get_first_commission(self) -> Tuple[str, int]:
        if len(self.commissions) > 0:
            return self.commissions[0]
        else:
            return None, None

    def run(self):
        self.go_to(screen="main")
        self._build_priorities()
        if len(self.commissions) == 0:
            return None

        building, fundraise = self._get_first_commission()
        waiting_time = self._build(building, fundraise)
        return waiting_time

    def _build_priorities(
        self, path: Path = Path("data/build_to_prevent.json")
    ):
        with open(path, "r") as file:
            priorities_order = json.load(file)

        self._build_priority(priorities_order, "farm")
        self._build_priority(priorities_order, "storage")

        with open(path, "w") as file:
            json.dump(priorities_order, file)

    def _build_priority(self, priorities_order: dict, building: Literal["farm", "storage"]):
        if building == "farm":
            max_depth = 2
        elif building == "storage":
            max_depth = 1
        if priorities_order[building] in ["1", "True", 1, True]\
                and priorities_order[building + "_in_process"] not in ["1", "True", 1, True]:
            self._add_commission(building, 1)
            priorities_order[building] = False
            priorities_order[building + "_in_process"] = True
        elif priorities_order[building + "_in_process"]\
                and not self._building_in_plans(building, max_depth=max_depth):
            priorities_order[building + "_in_process"] = False

    def _building_in_plans(
        self, building: str, max_depth: int = None
    ):
        in_plan = self._building_in_plan_queue(building, max_depth)
        in_process = self._building_in_process_queue(building)
        return in_plan or in_process

    def _building_in_plan_queue(
        self, building: str, max_depth: int = None
    ):
        if max_depth is None:
            max_depth = len(self.commissions)
        res = False
        for depth in range(max_depth):
            res = res or self.commissions[depth][0] == building
        return res

    def _building_in_process_queue(self, building: str):
        els = self.driver.find_elements(
            By.XPATH, '//*[@id="buildqueue"]//img[contains(@src, "%s")]' % building)
        return len(els) > 0

    def _skip_first_commission(self):
        self._remove_first_commission()
        logging.warning("Removing first commission.")

        building, fundraise = self._get_first_commission()
        time_delta = self._build(building, fundraise)
        return time_delta

    def _deal_with_unmet_requirements(self, building: str):
        logging.warning('Unmet requirements for building "%s". ' % building)
        els = self.driver.find_elements(By.XPATH, '//*[@id="buildqueue"]/tr[2]/td[2]/span')
        if len(els) > 0:
            delta_str = els[0].text
            time_delta = self._str_to_timedelta(delta_str)
            logging.warning("Waiting until last building is built.")
        else:
            time_delta = self._skip_first_commission()
        return time_delta

    def _build(self, building: str, fundraise: Union[str, int, bool]) -> timedelta:
        can_run = self._assert_build(building)
        waiting_time = self._get_waiting_time(building)

        if can_run:
            self.commission_building(building)
        elif self._unknown_building(building):
            logging.warning('Unknown building "%s".' % building)
            waiting_time = self._skip_first_commission()
        elif self._unmet_requirements(building):
            waiting_time = self._deal_with_unmet_requirements(building)
        elif self._requirements_over_90_percents(building)\
                and building != "storage":
            self._add_commission("storage", "1")
            waiting_time = self._build("storage", "1")
        elif fundraise == '1' or fundraise == 1 or fundraise is True:
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
