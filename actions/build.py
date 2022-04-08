import csv
from curses.ascii import CAN
from datetime import datetime, timedelta
import json
import logging
import re
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from typing import Literal, List, Union, Tuple, Optional

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Cost

(CAN_BUILD, FULL_QUEUE, LACK_OF_RESOURCES, LACK_OF_VILLAGERS,\
    UNMET_REQUIREMENTS, UNKNOWN_BUILDING, FULLY_DEVELOPED) = tuple(range(7))


class Build(Action):
    def __init__(
        self,
        input_: ActionInput,
        allow_time_reducing: bool = False
    ):
        super().__init__(input_)
        self.path = self.base_path / 'build.csv'
        self.build_to_prevent_path = self.base_path / 'build_to_prevent.json'
        with open(self.path, "r") as file:
            commissions = list(csv.reader(file))
        self.commissions = commissions
        self.allow_time_reducing = allow_time_reducing

    def _commission_building(self, building: str, max_time: timedelta = None):
        self.sleep()

        def commit(y_pos: int) -> bool:
            self.driver.execute_script("window.scrollTo(0, %d)" % y_pos)
            try:
                self.driver.find_element(
                    By.XPATH,
                    '//a[(contains(text(), "Poziom") or contains(text(), "Wybuduj")) '\
                    'and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
                ).click()
                return True
            except:
                return False

        commited = commit(y_pos=0)
        if not commited:
            commited = commit(y_pos=500)
        if not commited:
            commited = commit(y_pos=1000)
        if not commited:
            raise NoSuchElementException('Cannot click on building "%s".' % building)

        self.driver.execute_script("window.scrollTo(0, 0)")
        self._remove_first_commission()

        self.sleep()
        self._reduce_time(max_time, building)
        waiting_time = self._get_building_time(0)
        return waiting_time

    def _reduce_time(self, max_time: timedelta, building: str):
        time_ = self._get_building_time(pos=-1)
        while self._if_reduce_time(time_, max_time):
            self._commit_time_reduction(pos=-1)

            self.sleep()
            old_time_ = time_
            time_ = self._get_building_time(pos=-1)
            self.log(
                'Time of buliding "%s" reduced from %s to %s'\
                % (building, str(old_time_), str(time_)))
        return time_

    def _if_reduce_time(self, waiting_time: timedelta, max_time: timedelta = None) -> bool:
        enough_pp = self._get_pp() > self.pp_limit
        return (
            self.allow_time_reducing
            and max_time is not None
            and waiting_time > max_time
            and enough_pp
        )

    def _get_building_time(self, pos: int) -> timedelta:
        els = self.driver.find_elements(By.XPATH, '//*[@id="buildqueue"]/tr/td[2]/span')
        time_delta = self._str_to_timedelta(els[pos].text)
        return time_delta

    def _commit_time_reduction(self, pos: int):
        self.sleep()
        els = self.driver.find_elements(By.XPATH, '//*[@id="buildqueue"]/tr/td[3]/a[1]')
        els[pos].click()

        self.sleep()
        els = self.driver.find_elements(By.XPATH, '//*[@id="pp_prompt"]')
        if len(els) > 0:
            if els[0].is_selected():
                els[0].click()

            self.sleep()
            self.driver.find_element(
                By.XPATH, '//*[@id="confirmation-box"]//button[contains(text(),"Potwierdź")]'
            ).click()

    def _remove_first_commission(self) -> List:
        row = self.commissions.pop(0)
        with open(self.path, "w") as file:
            csv.writer(file).writerows(
                self.commissions)
        if len(row) < 3:
            row += [None]
        return row

    def _can_build(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//a[(contains(text(), "Poziom") or contains(text(), "Wybuduj")) '\
            'and contains(@id, "main_buildlink_%s") and not (@style="display:none")]' % building
        )
        return len(els) > 0

    def _queue_is_full(self):
        els = self.driver.find_elements(
            By.XPATH,
            '//*[@id="buildqueue"]/tr'
        )
        return len(els) == 4

    def _lack_of_resources(self, building: str):
        lack_of_resources_elements = self.driver.find_elements(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Surowce dostępne")]' % building
        )
        return len(lack_of_resources_elements) > 0

    def _lack_of_villagers(self, building: str) -> bool:
        lack_of_resources_elements = self.driver.find_elements(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Zagroda za mała")]' % building
        )
        return len(lack_of_resources_elements) > 0

    def _unmet_requirements(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//*[@id="buildings_unmet"]/tbody//a[contains(@href, "%s")]' % building)
        return len(els) > 0

    def _fully_developed(self, building: str):
        els = self.driver.find_elements(
            By.XPATH,
            '//*[@id="main_buildrow_%s"]/td' % building)
        return len(els) == 2

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

    def _assert_build(self, building: str) -> int:
        if self._can_build(building):
            return CAN_BUILD
        elif self._queue_is_full():
            return FULL_QUEUE
        elif self._lack_of_resources(building):
            return LACK_OF_RESOURCES
        elif self._lack_of_villagers(building):
            return LACK_OF_VILLAGERS
        elif self._unmet_requirements(building):
            return UNMET_REQUIREMENTS
        elif self._unknown_building(building):
            return UNKNOWN_BUILDING
        elif self._fully_developed(building):
            return FULLY_DEVELOPED
        else:
            self._raise_unknown_limitation_error(building)

    def _get_waiting_time(self, building: str, state: int) -> timedelta:
        # if state == CAN_BUILD:
        #     delta = self.driver.find_element(
        #         By.XPATH,
        #         '//*[@id="main_buildrow_%s"]/td[5]' % building
        #     ).text
        #     waiting_time = self._str_to_timedelta(delta)
        if state == CAN_BUILD or state == FULL_QUEUE or state == UNMET_REQUIREMENTS:
            els = self.driver.find_elements(
                By.XPATH,
                '//*[@id="buildqueue"]/tr[2]/td[2]/span[@data-endtime]'
            )
            if len(els) > 0:
                delta = els[0].text
                waiting_time = self._str_to_timedelta(delta)
            else:
                waiting_time = None
        elif state == LACK_OF_RESOURCES:
            text = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[7]/div[contains(text(), "Surowce dostępne")]' % building
            ).text
            if len(re.findall('dzisiaj', text)) > 0:
                waiting_time = datetime.now()
            elif len(re.findall('jutro', text)) > 0:
                waiting_time = datetime.now() + timedelta(days=1)
            elif len(re.findall('\d\d:\d\d:\d\d', text)) > 0:
                delta = self._str_to_timedelta(text[-8:])
                waiting_time = datetime.now() + delta
            else:
                raise ValueError("!!! Unknown text: %s" % text)
            waiting_time = waiting_time.replace(hour=int(text[-5:-3]))
            waiting_time = waiting_time.replace(minute=int(text[-2:]))
        elif state == FULLY_DEVELOPED:
            waiting_time = None
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
        row = None
        while len(self.commissions) > 0 and row is None:
            row = self.commissions[0]
            if len(row) == 2:
                row += [None]
            elif len(row) not in [2, 3]:
                raise ValueError('Wrong number of arguments: "%s".' % str(row))
        return row

    def run(self):
        self.go_to(screen="main")
        self._build_priorities()

        waiting_time, state = self._build_first_commission()
        if state == CAN_BUILD and not self._queue_is_full():
            self._build_first_commission()
        return waiting_time

    def _build_priorities(
        self
    ):
        with open(self.build_to_prevent_path, "r") as file:
            priorities_order = json.load(file)

        self._build_priority(priorities_order, "farm")
        self._build_priority(priorities_order, "storage")

        with open(self.build_to_prevent_path, "w") as file:
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
        if max_depth is None or max_depth > len(self.commissions):
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
        self.log("Removing first commission.", logging.WARN)

    def _build_first_commission(self) -> Tuple[timedelta, int]:
        row = self._get_first_commission()
        if row is None:
            waiting_time, state = None, None
        else:
            waiting_time, state = self._build(row)
        return waiting_time, state

    def _deal_with_unmet_requirements(self, building: str):
        self.log(
            'Unmet requirements for building "%s". ' % building,
            logging.WARN)
        waiting_time = self._get_waiting_time(building, state=UNMET_REQUIREMENTS)
        if waiting_time is None:
            self._skip_first_commission()
            waiting_time, state = self._build_first_commission()
        else:
            self.log("Waiting until last building is built.", logging.INFO)
            state = UNMET_REQUIREMENTS
        return waiting_time, state

    def _deal_with_lack_of_resources(self, building: str, fundraise: Union[str, int, bool]) -> Optional[timedelta]:
        if self._requirements_over_90_percents(building) and building != "storage":
            self._add_commission("storage", "1")
            waiting_time, state = self._build_first_commission()
        elif fundraise == '1' or fundraise == 1 or fundraise is True:
            self.set_fundraise(
                self._get_building_cost(building), type(self)
            )
            waiting_time = self._get_waiting_time(building, state=LACK_OF_RESOURCES)
            state = LACK_OF_RESOURCES
        return waiting_time, state

    def _deal_with_lack_of_villagers(self, building: str, fundraise: Union[str, int, bool]) -> Optional[timedelta]:
        pass

    def _build(self, row: Tuple[str, Union[str, int, bool], int]) -> Tuple[timedelta, int]:
        self.sleep()
        building, fundraise, max_time = row
        state = self._assert_build(building)

        if state == CAN_BUILD:
            if max_time is not None:
                max_time = self._str_to_timedelta(max_time)
            waiting_time = self._commission_building(building, max_time)
        elif state == FULL_QUEUE:
            waiting_time = self._get_waiting_time(building, state)
        elif state == UNKNOWN_BUILDING:
            self.log('Unknown building "%s".' % building, logging.WARN)
            self._skip_first_commission()
            waiting_time, state = self._build_first_commission()
        elif state == FULLY_DEVELOPED:
            self.log('Building "%s" is fully developed.' % building, logging.INFO)
            waiting_time = self._skip_first_commission()
            waiting_time, state = self._build_first_commission()
        elif state == UNMET_REQUIREMENTS:
            waiting_time, state = self._deal_with_unmet_requirements(building)
        elif state == LACK_OF_RESOURCES:
            waiting_time, state = self._deal_with_lack_of_resources(building, fundraise)
        elif state == LACK_OF_VILLAGERS:
            waiting_time = self._get_waiting_time(building, state)
        return waiting_time, state

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
