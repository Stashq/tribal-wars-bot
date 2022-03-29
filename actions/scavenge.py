from dataclasses import asdict
from datetime import datetime, timedelta
import json
from selenium.webdriver.common.by import By
from pathlib import Path
from typing import List, Tuple

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Scavengers
from tactics.scavenge import ScavengeTactic


units_to_input_parser = {
    "spear": 1, "sword": 2, "axe": 3, "archer": 4,
    "light": 5, "marcher": 6, "heavy": 7, "knight": 8
}

int_to_unit_td_parser = {
    0: 1, 1: 2, 2: 3, 3: 4, 4: 6, 5: 7, 6: 8, 7: 11
}


class Scavenge(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)

    def load_tactic(self, path: Path = Path("data/scavenge.json")):
        with open(path, "r") as file:
            tactic = json.load(file)
        lvls = self._filter_lvls(tactic["lvls"])
        tactic = ScavengeTactic(
            divide=tactic["divide"],
            lvls=lvls,
            except_=Scavengers(**tactic.get("except_", {})),
            troops_lvl1=Scavengers(**tactic.get("lvl1", {})),
            troops_lvl2=Scavengers(**tactic.get("lvl2", {})),
            troops_lvl3=Scavengers(**tactic.get("lvl3", {})),
            troops_lvl4=Scavengers(**tactic.get("lvl4", {}))
        )
        self.time_after_attempt = timedelta(minutes=60)
        return tactic

    def _filter_lvls(self, lvls: List[int]):
        lvls = self._filter_unclocked_lvls(lvls)
        lvls = self._filter_available_lvls(lvls)
        return lvls

    def _filter_unclocked_lvls(self, lvls: List[int]):
        for lvl in range(1, 4):
            elements = self.driver.find_elements(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[text()="Odblokowanie"]' % lvl)
            if len(elements) > 0:
                lvls.remove(lvl)
        return lvls

    def _filter_available_lvls(self, lvls: List[int]):
        free_sessions = []
        for lvl in lvls:
            elements = self.driver.find_elements(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[1][text()="Start"]' % lvl)
            if len(elements) > 0:
                free_sessions += [lvl]
        return free_sessions

    def _run_scavenging(self, lvl: int, troops: Scavengers):
        if troops.is_empty():
            return
        self.sleep()
        for unit, amount in asdict(troops).items():
            index = units_to_input_parser[unit]

            self.sleep(mu=0.35)
            el = self.driver.find_element(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[1]/table/tbody/tr[2]/td[%d]/input' % index)
            el.send_keys(str(amount))

        self.sleep()
        el = self.driver.find_element(
            By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[1]' % lvl
        )
        el.click()

    def _get_waiting_time(self) -> timedelta:
        self.sleep(2)
        els = self.driver.find_elements(
            By.XPATH,
            '//*[@id="scavenge_screen"]/div/div[2]/div/div[3]/div/ul/li[4]/span[@class="return-countdown"]'
        )

        if len(els) == 0:
            waiting_time = self.time_after_attempt
        else:
            waiting_times = []
            for el in els:
                delta = datetime.strptime(el.text, "%H:%M:%S")
                delta = timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
                waiting_times += [delta]
                waiting_times = min(waiting_times)
        return waiting_time

    def _get_available_troops(self) -> Scavengers:
        units = [None] * 8
        for i in range(8):
            el = self.driver.find_element(
                By.XPATH,
                '//*[@id="units_home"]/tbody/tr[2]/td[%d]' % (int_to_unit_td_parser[i] + 3))
            units[i] = int(el.text)
        troops = Scavengers(*units)
        return troops

    def _transpored_troops_exists(self):
        els = self.driver.find_elements(By.XPATH, '//*[@id="units_transit"]')
        return len(els) > 0

    def _get_transported_troops(self):
        if self._transpored_troops_exists():
            units = [None] * 8
            for i in range(8):
                el = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="units_transit"]/tbody/tr[2]/td[%d]' % (int_to_unit_td_parser[i] + 1))
                units[i] = int(el.text)
            troops = Scavengers(*units)
        else:
            troops = Scavengers()
        return troops

    def _get_troops_info(self) -> Tuple[Scavengers, Scavengers]:
        available_troops = self._get_available_troops()
        transported_troops = self._get_transported_troops()
        return available_troops, transported_troops

    def run(self, path: Path = Path("data/scavenge.json"), *args, **kwargs) -> timedelta:
        self.go_to(screen="place", mode="units")
        available_troops, transported_troops = self._get_troops_info()

        self.change_mode(mode="scavenge")
        self.sleep()
        self.driver.execute_script("window.scrollTo(0, 884)")

        st = self.load_tactic(path)
        troops_per_lvl = st.get_troops_per_lvl(
            available_troops, transported_troops)
        for lvl, troops in troops_per_lvl.items():
            self._run_scavenging(lvl, troops)

        waiting_time = self._get_waiting_time()
        return waiting_time
