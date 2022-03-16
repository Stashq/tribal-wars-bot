from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import dotenv_values
import time
import numpy as np
from typing import List, Iterable, Union, Type
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import logging
import csv
from selenium.webdriver.remote.command import Command

from actions import Scavenge, ActionInput, Action, Train, Build
from data_types import Cost
from scheduler import Scheduler


class Bot:
    def __init__(self, world_nr: int = 175):
        logging.basicConfig(
            filename='scavegning.log',
            format='%(asctime)s : %(message)s',
            level=logging.INFO
        )
        self.driver = None
        self.current_village_url = None
        self.fundraise = {"cost": Cost(), "action": None}
        self.world_nr = world_nr
        self.scheduler = Scheduler()

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
            # print("Already logged in")
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

    # def set_fundraise(self, wood: int, stone: int, iron: int, cmd: List[str]):
    #     self.fundraise_cmd = cmd
    #     self.fundraise = [wood, stone, iron]
    #     logging.info(
    #         "Set fundraise: wood %d, stone %d, iron %d." % (wood, stone, iron)
    #     )

    # def unset_fundraise(self):
    #     self.fundraise_cmd = []
    #     self.fundraise = [0, 0, 0]
    #     logging.info("Fundraise unset.")

    # def run_cmd(self, cmd: List[str]) -> bool:
    #     try:
    #         func = getattr(self, cmd[0])
    #         runned = func(*cmd[1:])
    #         if runned and self.compare_cmds(self.fundraise_cmd, cmd):
    #             self.unset_fundraise()
    #     except Exception as e:
    #         runned = None
        
        # self.log_priority_run(runned, cmd)
        # return runned

    def compare_cmds(self, cmd1: List, cmd2: List) -> bool:
        if isinstance(cmd1, Iterable):
            cmd1 = [str(el) for el in cmd1]
        if isinstance(cmd2, Iterable):
            cmd2 = [str(el) for el in cmd2]
        return str(cmd1) == str(cmd2)

    def run_priorities(self, n: int = 1, break_after_fail: bool = True):
        with open('priorities.csv', "r") as file:
            cmds = list(csv.reader(file))

        for i in range(n):
            if len(cmds) == 0:
                break

            runned = self.run_cmd(cmds[0])

            if runned:
                cmds = cmds[1:]
            elif not runned and break_after_fail:
                break

        with open('priorities.csv', "w") as file:
            csv.writer(file).writerows(cmds)

    def log_priority_run(self, runned: bool, cmd: str):
        if runned:
            logging.info("Priority: \"%s\" runned [v]" % str(cmd))
        elif runned is False:
            logging.warning("Priority: \"%s\" failed [x]" % str(cmd))
        elif runned is None:
            logging.warning("Problem with running priority \"%s\"." % str(cmd))

    def setup_next_visit_time(
        self,
        time_: Union[datetime, timedelta],
        action: Action,
        additional_minutes: int = 0
    ):
        time_ = time_ + timedelta(minutes=additional_minutes)
        self.scheduler.set_waiting_time(time_, action)

    def quit_session(self):
        self.sleep(2)
        self.driver.quit()
        self.scheduler.log_times()
        logging.info("Driver quited session.")

    def run_rutines(self):
        if self.scheduler.train is None:
            self.run_action(Train)
        if self.scheduler.build is None:
            self.run_action(Build)
        if self.scheduler.scavenge is None:
            self.run_action(Scavenge)

    def run_cycle(self):
        action = self.scheduler.wait()
        self.init_driver()
        self.login(world_nr=175)
        self.run_action(action)
        self.run_rutines()
        self.quit_session()

    def first_run(self):
        self.init_driver()
        self.login(world_nr=175)
        self.run_rutines()
        self.quit_session()

    def run_action(self, Action_cls: Type[Action]):
        ai = ActionInput(
            driver=self.driver,
            world_nr=self.world_nr,
            village_nr=175,
            fundraise=self.fundraise,
            # fundraise_action=self.fundraise_action
        )
        action = Action_cls(ai)
        time_ = action.run()
        if time_ is not None:
            self.setup_next_visit_time(time_, action)
        if self.fundraise["action"] == Action_cls:
            self._reset_fundraise()

    def _reset_fundraise(self):
        self.fundraise["cost"] = Cost()
        self.fundraise["action"] = None

    def log_error(self):
        logging.error("Error! [x]")
        try:
            self.driver.save_screenshot("screenshot.png")
            logging.error("Screenshot took.")
        except Exception as e:
            pass

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
            self.log_error()
            raise e
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt.")
        finally:
            self.quit_run()
