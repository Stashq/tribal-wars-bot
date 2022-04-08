from dotenv import dotenv_values
from datetime import datetime
import inspect
import logging
import numpy as np
import os
import pause
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
import time
import traceback
from typing import Union, Type
from webdriver_manager.chrome import ChromeDriverManager

from actions import Action, Build, Farm, Recruit, Scavenge, Train
from check_data import FilesChecker
from village_caretaker import VillageCaretaker


class Deputy:
    def __init__(
        self,
        world_nr: int = 175,
        safe_mode: bool = True,
        allow_time_reducing = False,
        pp_limit: int = 9999999
    ):
        logging.basicConfig(
            filename='bot_run.log',
            format='%(asctime)s : %(message)s',
            level=logging.INFO
        )
        self.driver = None
        self.world_nr = world_nr
        self.safe_mode = safe_mode
        self.allow_time_reducing = allow_time_reducing
        self.pp_limit = pp_limit
        self.village_caretakers = self.create_village_caretakers()

    def create_village_caretakers(self):
        villages = self.get_declared_villages()
        res = [
            VillageCaretaker(
                driver=self.driver,
                village_coordinates=v_cor,
                base_url='https://pl%d.plemiona.pl/game.php?screen=overview_villages' % self.world_nr,
                safe_mode=self.safe_mode,
                pp_limit=self.pp_limit
            )
            for v_cor in villages
        ]
        return res

    def get_declared_villages(self):
        villages = os.listdir('villages_commissions')
        villages = list(filter(
            lambda v: 
                os.path.isdir('villages_commissions/' + v),
            villages
        ))
        return villages

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
                    version="100.0.4896.60",
                    print_first_line=False,
                    log_level=logging.ERROR
                ).install()))
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent":
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36'})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

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

        self.prevent_captcha()

        self.choose_world(world_nr)
        time.sleep(2)

    def choose_world(self, world_nr: int = 175):
        # url = '/page/play/pl' + str(world_nr)
        self.sleep()
        # self.driver.find_element(By.XPATH, '//a[@href="'+url+'"]')\
        #     .click()
        self.driver.find_element(By.XPATH, '//*[@id="home"]/div[3]/div[4]/div[10]/div[3]/div[2]/div[1]/a/span')\
            .click()

        self.prevent_captcha()

    def prevent_captcha(self):
        els = self.driver.find_elements(By.ID, 'popup_box_bot_protection')
        if len(els) > 0:
            print('Captcha detected.')
            checkbox = els[0].find_element(By.ID, 'checkbox')
            self.sleep()
            checkbox.click()
            self.sleep(3)

        els = self.driver.find_elements(By.CLASS_NAME, 'captcha')
        if len(els) > 0:
            print('Captcha detected.')
            checkbox = els[0].find_element(By.ID, 'checkbox')
            self.sleep()
            checkbox.click()
            self.sleep(3)

    def quit_session(self):
        self.sleep(2)
        self.driver.quit()
        self.log("Driver quited session.")

    def run_cycle(self):
        vc = self.wait()
        self.init_driver()
        self.login(world_nr=175)
        vc.run(self.driver)
        self.quit_session()

    def log_error(self, e: Exception):
        self.log("Error! [x]", logging.ERROR)
        logging.exception(e)
        traceback.print_exc()
        if self._driver_is_alive():
            self.driver.save_screenshot(
                "error_screenshots/" + datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))
            self.log("Screenshot took.", logging.WARN)
        else:
            self.log("Driver is dead.", logging.WARN)

    def log(self, text: str, lvl: int = logging.INFO):
        logging.log(lvl, text)

    def _action_to_str(self, action: Union[Action, Type[Action]]) -> str:
        if inspect.isclass(action):
            action_type = action
        else:
            action_type = type(action)
        if action_type == Build:
            cmd = "build"
        elif action_type == Farm:
            cmd = "farm"
        elif action_type == Recruit:
            cmd = "recruit"
        elif action_type == Scavenge:
            cmd = "scavenge"
        elif action_type == Train:
            cmd = "train"
        else:
            raise ValueError('Unknown action "%s"' % str(action_type))
        return cmd

    def wait(self) -> VillageCaretaker:
        vc = self.get_first_village_caretaker()
        self.log('Next run: (%s) %s %s.' % (
            vc.village_coordinates,
            self._action_to_str(vc.next_action),
            vc.next_time.strftime("%Y-%m-%d, %H:%M:%S")))
        pause.until(vc.next_time)
        return vc

    def get_first_village_caretaker(self) -> VillageCaretaker:
        first_vc = self.village_caretakers[0]
        for vc in self.village_caretakers[1:]:
            if vc.next_time < first_vc.next_time:
                first_vc = vc
        return first_vc

    def first_run(self):
        FilesChecker().check_all_files()
        self.init_driver()
        self.login(world_nr=175)
        for vc in self.village_caretakers:
            vc.run(self.driver)
        self.quit_session()

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
        self.log("Bot ends.")

    def run(self):
        self.log("====== New session ======")
        try:
            self.first_run()
            while True:
                self.run_cycle()
        except Exception as e:
            if not self.safe_mode:
                raise e
            self.log_error(e)
        except KeyboardInterrupt:
            self.log("Keyboard interrupt.")
        finally:
            self.quit_run()
