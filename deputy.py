from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import dotenv_values
import time
import numpy as np
import traceback
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import logging
import pause
from selenium.webdriver.remote.command import Command
import os

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
                    version="98.0.4758.102",
                    print_first_line=False,
                    log_level=logging.ERROR
                ).install()))
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent":
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'})
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

        self.choose_world(world_nr)
        time.sleep(2)

    def choose_world(self, world_nr: int = 175):
        # url = '/page/play/pl' + str(world_nr)
        self.sleep()
        # self.driver.find_element(By.XPATH, '//a[@href="'+url+'"]')\
        #     .click()
        self.driver.find_element(By.XPATH, '//*[@id="home"]/div[3]/div[4]/div[10]/div[3]/div[2]/div[1]/a/span')\
            .click()

    def quit_session(self):
        self.sleep(2)
        self.driver.quit()
        logging.info("Driver quited session.")

    def run_cycle(self):
        vc = self.wait()
        self.init_driver()
        self.login(world_nr=175)
        vc.run(self.driver)
        self.quit_session()

    def wait(self) -> VillageCaretaker:
        vc = self.get_first_village_caretaker()
        logging.info("Waiting until %s." % vc.next_time.strftime("%Y-%m-%d, %H:%M:%S"))
        pause.until(vc.next_time)
        return vc

    def get_first_village_caretaker(self) -> VillageCaretaker:
        first_vc = self.village_caretakers[0]
        for vc in self.village_caretakers[1:]:
            if vc.next_time < first_vc.next_time:
                first_vc = vc
        return vc

    def first_run(self):
        FilesChecker().check_all_files()
        self.init_driver()
        self.login(world_nr=175)
        for vc in self.village_caretakers:
            vc.run(self.driver)
        self.quit_session()

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
