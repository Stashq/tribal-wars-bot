from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import dotenv_values
import time
import numpy as np
import traceback
from typing import Union, Type
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import logging
from selenium.webdriver.remote.command import Command
from typing import Tuple, Dict

from actions import Scavenge, ActionInput, Action, Train, Build, Recruit, Farm, Prevent
from check_data import check_all_files
from data_types import Cost
from scheduler import Scheduler


class Bot:
    def __init__(
        self,
        world_nr: int = 175,
        safe_mode: bool = True,
        prevent: bool = True,
        allow_time_reducing = False,
        pp_limit: int = 9999999
    ):
        logging.basicConfig(
            filename='bot_run.log',
            format='%(asctime)s : %(message)s',
            level=logging.INFO
        )
        self.driver = None
        self.current_village_url = None
        self.fundraise = {"cost": Cost(), "action": None}
        self.world_nr = world_nr
        self.scheduler = Scheduler()
        self.safe_mode = safe_mode
        self.attempt_break = timedelta(hours=1)
        self.prevent = prevent
        self.allow_time_reducing = allow_time_reducing
        self.pp_limit = pp_limit

    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-data-dir=user_data")

        self.driver = webdriver.Chrome(
            options=options,
            service=Service(
                ChromeDriverManager(
                    version="98.0.4758.102",
                    print_first_line=False,
                    log_level=logging.ERROR
                ).install()))
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent":
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def sleep(self, mu: float = 1.345, sig: float = 0.35):
        rand = np.random.randn()
        time.sleep(
            abs(rand*sig + mu)
        )

    def login(self, world_nr: int = 175):
        config = dotenv_values(".env")
        self.driver.get('https://www.plemiona.pl/')
        try:
            self.sleep()
            self.driver.find_element(By.ID, 'user').send_keys(config['username'])
            self.sleep()
            self.driver.find_element(By.ID, 'password').send_keys(config['password'])
            self.sleep(0.3, 0.02)
            self.driver.find_element(By.XPATH, '//*[@id="login_form"]/div/div/a')\
                .click()
        except NoSuchElementException as e:
            pass

        self.choose_world(world_nr)
        time.sleep(2)
        self.current_village_url = self.driver.current_url

    def choose_world(self, world_nr: int = 175):
        # url = '/page/play/pl' + str(world_nr)
        self.sleep()
        # self.driver.find_element(By.XPATH, '//a[@href="'+url+'"]')\
        #     .click()
        self.driver.find_element(By.XPATH, '//*[@id="home"]/div[3]/div[4]/div[10]/div[3]/div[2]/div[1]/a/span')\
            .click()

    def setup_next_visit_time(
        self,
        action: Action,
        action_res: Union[timedelta, Tuple[timedelta, str], Dict[str, timedelta]],
    ):
        self.scheduler.set_waiting_time(action, action_res)

    def quit_session(self):
        self.sleep(2)
        self.driver.quit()
        self.scheduler.log_times()
        logging.info("Driver quited session.")

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

    def run_cycle(self):
        Action_, com_id = self.scheduler.wait()
        kwargs = self.get_action_kwargs(Action_, com_id)
        self.init_driver()
        self.login(world_nr=175)
        self.run_action(Action_, **kwargs)
        self.run_rutines()
        self.quit_session()

    def get_action_kwargs(self, Action_: Type[Action], com_id: str) -> Tuple[Tuple, Dict]:
        kwargs = {}
        if Action_ == Build:
            kwargs['allow_time_reducing'] = self.allow_time_reducing
        if com_id is not None:
            kwargs['com_id'] = com_id
        return kwargs

    def first_run(self):
        check_all_files()
        self.init_driver()
        self.login(world_nr=175)
        self.run_rutines()
        self.quit_session()

    def _deal_with_action_exception(self, e: Exception):
        if not self.safe_mode:
            raise e
        self.log_error(e)
        print("Continue running program...")
        time_ = self.attempt_break
        logging.info("Next attempt in " + str(time_))
        return time_

    def run_action(self, Action_cls: Type[Action], *args, **kwargs):
        ai = ActionInput(
            driver=self.driver,
            world_nr=self.world_nr,
            village_nr=175,
            fundraise=self.fundraise,
            pp_limit=self.pp_limit
        )
        action = Action_cls(ai, *args, **kwargs)
        try:
            res = action.run()
        except Exception as e:
            res = self._deal_with_action_exception(e)
            res = (res, kwargs.get('com_id'))
        if res is not None:
            self.setup_next_visit_time(action, res)
        if self.fundraise["action"] == Action_cls:
            self._reset_fundraise()

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

    def run(self):
        logging.info("====== New session ======")
        try:
            self.first_run()
            while True:
                self.run_cycle()
        except Exception as e:
            if not self.safe_mode:
                raise e
            self.log_error(e)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt.")
        finally:
            self.quit_run()
