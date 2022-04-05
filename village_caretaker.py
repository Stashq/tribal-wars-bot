from xmlrpc.client import Boolean
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import numpy as np
import traceback
from typing import Type
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime, timedelta
import logging
from selenium.webdriver.remote.command import Command
from typing import Tuple, Dict, List, Union

from actions import Scavenge, ActionInput, Action, Train, Build, Recruit, Farm, Prevent
from data_types import Cost
from scheduler import Scheduler


class VillageCaretaker:
    def __init__(
        self,
        driver: webdriver,
        village_coordinates: str,
        base_url = str,
        safe_mode: bool = True,
        prevent: bool = True,
        allow_time_reducing = False,
        pp_limit: int = 9999999
    ):
        self.current_village_url = None
        self.next_action = None
        self.next_time = None
        self.next_com_id = None

        self.base_url = base_url
        self.driver = driver
        self.village_coordinates = village_coordinates
        self.fundraise = {"cost": Cost(), "action": None}
        self.scheduler = Scheduler()
        self.safe_mode = safe_mode
        self.attempt_break = timedelta(hours=1)
        self.prevent = prevent
        self.allow_time_reducing = allow_time_reducing
        self.pp_limit = pp_limit

    def sleep(self, mu: float = 2, sig: float = 0.35):
        rand = np.random.randn()
        time.sleep(
            abs(rand*sig + mu)
        )

    def run_rutines(self):
        if self.prevent:
            self.run_action(Prevent)

        if self.scheduler.train is None:
            self.run_action(Train)
        if self.scheduler.build is None:
            self.run_action(
                Build,
                allow_time_reducing=self.allow_time_reducing)
        if self.scheduler.scavenge is None:
            self.run_action(Scavenge)
        if self.scheduler.recruit is None:
            self.run_action(Recruit)
        if self.scheduler.farm is None:
            self.run_action(Farm)

    def set_next_task(self):
        Action_cls, next_time, com_id = self.scheduler.get_earliest_task()
        self.next_action = Action_cls
        self.next_time = next_time
        self.next_com_id = com_id

    def create_action_kwargs(self, Action_cls: Type[Action], com_id: str) -> Dict['str', Union[Boolean, str]]:
        kwargs = {}
        if Action_cls == Build:
            kwargs['allow_time_reducing'] = self.allow_time_reducing
        if com_id is not None:
            kwargs['com_id'] = com_id
        return kwargs

    def _deal_with_action_exception(self, e: Exception):
        if not self.safe_mode:
            raise e
        self.log_error(e)
        print("Continue running program...")
        time_ = self.attempt_break
        logging.info("Next attempt in " + str(time_))
        return time_

    def run_action(self, Action_cls: Type[Action], **action_kwargs):
        ai = ActionInput(
            driver=self.driver,
            village_coordinates=self.village_coordinates,
            current_village_url=self.current_village_url,
            fundraise=self.fundraise,
            pp_limit=self.pp_limit
        )
        action = Action_cls(ai, **action_kwargs)
        try:
            res = action.run()
        except Exception as e:
            res = self._deal_with_action_exception(e)
            res = (res, action_kwargs.get('com_id'))
        if res is not None:
            self.scheduler.set_waiting_time(action, res)
        if self.fundraise["action"] == Action_cls:
            self._reset_fundraise()
        return res

    def _parse_action_res(self, res) -> Tuple[timedelta, str]:
        try:
            time_, com_id = res
        except:
            time_ = res
            com_id = None
        return time_, com_id

    def _reset_fundraise(self):
        self.fundraise["cost"] = Cost()
        self.fundraise["action"] = None

    def log_error(self, e: Exception):
        logging.error("Error! [x]")
        logging.exception(e)
        traceback.print_exc()
        if self._driver_is_alive():
            self.driver.save_screenshot(
                "error_screenshots/" + datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))
            logging.warning("Screenshot took.")
        else:
            logging.warning("Driver is dead.")

    def _driver_is_alive(self) -> bool:
        try:
            self.driver.execute(Command.STATUS)
            result = True
        except Exception as e:
            result = False
        return result

    def quit_run(self):
        if self._driver_is_alive():
            self.quit_session()
        logging.info("Bot ends.")

    def run(self, driver: webdriver):
        self.driver = driver
        self._go_to_village()
        if self.next_action is not None:
            Action_cls = self.next_action
            action_kwargs = self.create_action_kwargs(
                Action_cls=self.next_action, com_id=self.next_com_id)
            self.run_action(Action_cls, **action_kwargs)
        self.run_rutines()
        self.set_next_task()
        self.scheduler.log_times(self.village_coordinates)
        return self.next_time

    def _go_to_village(self):
        self.sleep()
        self.driver.get(self.base_url)
        links = self.driver.find_elements(By.XPATH, '//*[@id="production_table"]/tbody/tr/td[1]/span/span/a[1]')
        if len(links) == 0 and not self._in_right_village():
            raise ValueError('Unknown village %s.' % self.village_coordinates)
        
        link = self._select_current_village(links)
        if link is None:
            raise ValueError('Unknown village %s.' % self.village_coordinates)
        
        link.click()
        if self.current_village_url is None:
            self.current_village_url = self.driver.current_url

    def _in_right_village(self):
        els = self.driver.find_element(
            By.XPATH, '//*[@id="menu_row2"]/td[2]/b[contains(text(), "%s")]'\
                % self.village_coordinates)
        return len(els) > 0

    def _select_current_village(self, links: List[WebElement]):
        res = None
        for link in links:
            els = link.find_elements(By.XPATH, 'span[contains(text(), "%s")]'\
                % self.village_coordinates)
            if len(els) > 0:
                res = link
        return res