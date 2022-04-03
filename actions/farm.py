from dataclasses import fields
from datetime import timedelta
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from typing import Dict, Union

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Troops
from tactics import FarmTactic
from tactics.farm import FarmCommission


class Farm(Action):
    def __init__(self, input_: ActionInput, com_id: str = None):
        super().__init__(input_)
        self.com_id = com_id
        self.fs = self._read_farm_file()
        self.next_attempt = timedelta(hours=2)

    def run(self) -> Union[timedelta, Dict[str, timedelta]]:
        self.go_to('place')
        if not self.fs.run:
            waiting_times = self.next_attempt
        elif self.com_id is not None:
            waiting_times = self._run_single_commission(self.com_id)
        else:
            waiting_times = self._run_all_commissions()
        return waiting_times

    def _enough_troops(self, troops: Troops):
        available = self._get_available_troops()
        return troops <= available

    def _run_commission(self, com: FarmCommission):
        if com.troops.is_empty() or\
            (not self._enough_troops(com.troops)
                and not com.send_incomplete):
            waiting_time = com.next_attempt
        else:
            troops = self._limit_troops(com.troops)
            self._select_troops(troops)
            self._attack(x=com.x, y=com.y)
            waiting_time = self._get_waiting_time(com.max_time)
            self._commit()
        return waiting_time

    def _run_single_commission(self, com_id: str) -> Dict[str, Union[timedelta, str]]:
        waiting_times = {}
        for com in self.fs.commissions:
            if com.id_ == com_id:
                waiting_times[com.id_] = self._run_commission(com)
            else:
                waiting_times[com.id_] = 'same'
        return waiting_times

    def _run_all_commissions(self):
        waiting_times = {}
        for com in self.fs.commissions:
            waiting_times[com.id_] = self._run_commission(com)
        return waiting_times

    def _read_farm_file(self, path: Path = Path('data/farm.json')):
        with open(path, 'r') as file:
            fs = json.load(file)
        fs = FarmTactic(**fs)
        return fs

    def _select_troops(self, troops: Troops):
        for unit in fields(Troops):
            val = getattr(troops, unit.name)
            if val > 0:
                self.sleep(0.3)
                self.driver.find_element(
                    By.XPATH, '//*[@id="unit_input_%s"]' % unit.name
                ).send_keys(
                    str(val)
                )

    def _get_available_troops(self):
        res = Troops()

        for unit in fields(Troops):
            text = self.driver.find_element(
                By.XPATH, '//*[@id="units_entry_all_%s"]' % unit.name).text
            val = int(text[1:-1].replace('.', ''))
            setattr(res, unit.name, val)
        return res

    def _limit_troops(self, troops: Troops):
        available = self._get_available_troops()
        available = available.subtract(self.fs.except_)
        res = troops.limit(available)
        return res

    def _attack(self, x: int, y: int):
        self.sleep(0.5)
        # select coordinates option
        self.driver.find_element(
            By.XPATH, '//*[@id="command_target"]//label[1]/input'
        ).click()
        
        self.sleep(0.5)
        # set coordinates
        self.driver.find_element(
            By.XPATH, '//*[@id="place_target"]/input'
        ).send_keys('%d|%d' % (x, y))

        self.sleep(0.5)
        # click on 'attack' to go to next page
        self.driver.find_element(
            By.XPATH, '//*[@id="target_attack"]'
        ).click()

    def _get_waiting_time(self, max_time: timedelta = None) -> timedelta:
        self.sleep()
        text = self.driver.find_element(
            By.XPATH,
            '//*[@id="command-data-form"]/div[1]/table/tbody/tr[3]/td[2]'
        ).text
        waiting_time = self._str_to_timedelta(text)
        if max_time is not None and waiting_time > max_time:
            waiting_time = max_time
        return waiting_time

    def _commit(self):
        self.sleep()
        self.driver.find_element(
            By.XPATH, '//*[@id="troop_confirm_submit"]'
        ).click()
