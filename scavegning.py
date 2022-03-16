from typing import Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import dotenv_values
import time
import numpy as np
from typing import List, Union, Iterable
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import pause
import logging
import json
from dataclasses import dataclass, asdict
import csv


WOOD = 0
STONE = 1
IRON = 2


def sleep_(mu: float = 1.345, sig: float = 0.35):
    rand = np.random.randn()
    time.sleep(
        abs(rand*sig + mu)
    )

@dataclass
class Barracks:
    spear: int = 0
    sword: int = 0
    axe: int = 0
    arch: int = 0

@dataclass
class Stable:
    spy: int = 0
    light: int = 0
    ma: int = 0
    hc: int = 0

@dataclass
class Workshop:
    ram: int = 0
    catapult: int = 0

@dataclass
class Recruitment:
    barracks: Barracks = Barracks()
    stable: Stable = Stable()
    workshop: Workshop = Workshop()


class Scavenging:
    def __init__(self, loop: bool = True):
        logging.basicConfig(
            filename='scavegning.log',
            format='%(asctime)s : %(message)s',
            level=logging.INFO
        )
        self.driver = None
        self.actions = None
        self.current_village_url = None
        self.next_visit_time = None
        self.fundraise = [0, 0, 0]
        self.fundraise_cmd = []
        self.loop = loop

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
                    log_level=0,
                    print_first_line=False
                ).install()))
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent":
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.actions = ActionChains(self.driver)

    def login(self, world_nr: int = 175):
        config = dotenv_values(".env")
        self.driver.get('https://www.plemiona.pl/')
        try:
            sleep_()
            self.driver.find_element(By.ID, 'user').send_keys(config['username'])
            sleep_()
            self.driver.find_element(By.ID, 'password').send_keys(config['password'])
            sleep_(0.3, 0.02)
            self.driver.find_element(By.XPATH, '//*[@id="login_form"]/div/div/a')\
                .click()
        except NoSuchElementException as e:
            print("Already logged in")

        self.choose_world(world_nr)
        time.sleep(2)
        self.current_village_url = self.driver.current_url

    def choose_world(self, world_nr: int = 175):
        # url = '/page/play/pl' + str(world_nr)
        sleep_()
        # self.driver.find_element(By.XPATH, '//a[@href="'+url+'"]')\
        #     .click()
        self.driver.find_element(By.XPATH, '//*[@id="home"]/div[3]/div[4]/div[10]/div[3]/div[2]/div[1]/a/span')\
            .click()

    def scavenge(self, lvls: List[int] = [2, 3, 4], knight: bool = True):
        # splits equally troops for all provided scavenge lvls
        self.go_to(screen="place", mode="scavenge")
        self.driver.execute_script("window.scrollTo(0, 884)")

        # check if lvl is locked
        sleep_(0.7)
        for lvl in lvls:
            elements = self.driver.find_elements(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[text()="Odblokowanie"]' % lvl)
            if len(elements) > 0:
                lvls.remove(lvl)

        # find free sessions
        free_sessions = []
        for lvl in lvls:
            elements = self.driver.find_elements(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[1][text()="Start"]' % lvl)
            if len(elements) > 0:
                free_sessions += [lvl]

        # get units amounts
        units = [None] * 8
        for i in range(1, 9):
            el = self.driver.find_element(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[1]/table/tbody/tr[2]/td[%d]/a' % i)
            units[i-1] = int(el.text[1:-1])
        if not knight:
            units[-1] = 0

        # splits units and run sessions
        for lvl in free_sessions:
            sleep_(2)
            for i in range(1, 9):
                amount = int(units[i-1]/len(free_sessions))
                # last get all remaining troops
                if lvl + 1 == max(free_sessions):
                    amount = units[i-1] - amount * (len(free_sessions) - 1)

                el = self.driver.find_element(
                    By.XPATH, '//*[@id="scavenge_screen"]/div/div[1]/table/tbody/tr[2]/td[%d]/input' % i)
                el.send_keys(str(amount))

            waiting_time = self.driver.find_element(
                By.XPATH,
                '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[1]/ul/li[4]/span[2]' % lvl
            ).text
            sleep_()
            self.driver.find_element(
                By.XPATH, '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/div[2]/a[1]' % lvl
            ).click()
            logging.info("Scavenge lvl %d started and will last %s" % (lvl, waiting_time))

        # collect waiting times
        sleep_(2)
        waiting_times = []
        for lvl in lvls:
            try:
                waiting_time = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="scavenge_screen"]/div/div[2]/div[%d]/div[3]/div/ul/li[4]/span[2]' % lvl
                ).text

                delta = datetime.strptime(waiting_time, "%H:%M:%S")
                delta = timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
                waiting_times += [delta]
            except:
                logging.warning("Cannot find remaining scavenging time.")

        # set earliest next visit time
        if self.loop:
            self.setup_next_visit_time(
                min(waiting_times))

    def get_resources(self, include_fundraise: bool = False) -> List[int]:
        '''Returns order: wood, stone, iron'''
        resources = [
            int(self.driver.find_element(By.CSS_SELECTOR, '#wood').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#stone').text),
            int(self.driver.find_element(By.CSS_SELECTOR, '#iron').text)
        ]

        # substract established fundraise
        if not include_fundraise:
            for i in range(len(resources)):
                resources[i] -= self.fundraise[i]
                if resources[i] < 0:
                    resources[i] = 0
        return resources

    def recruit_proportionally(
        self, rec_prop: Recruitment = None, path: str = "./recruit_proportions.json"
    ):
        if rec_prop is None:
            with open(path) as f:
                rec_prop = json.loads(f.read())
                rec_prop = Recruitment(
                    Barracks(**rec_prop["barracks"]),
                    Stable(**rec_prop["stable"]),
                    Workshop(**rec_prop["workshop"])
                )

        with open("costs.json") as f:
            costs = json.loads(f.read())

        rec_prop = asdict(rec_prop)
        requirements = [0, 0, 0]
        for building, units in rec_prop.items():
            for unit, proportion in units.items():
                requirements[WOOD] += costs[unit][WOOD] * proportion
                requirements[STONE] += costs[unit][STONE] * proportion
                requirements[IRON] += costs[unit][IRON] * proportion
        
        wood, stone, iron = self.get_resources()
        n_packs = int(min([
            wood / requirements[WOOD], stone / requirements[STONE], iron / requirements[IRON]
        ]))

        rec = Recruitment(
            Barracks(**{unit: n_packs * amount for unit, amount in rec_prop["barracks"].items()}),
            Stable(**{unit: n_packs * amount for unit, amount in rec_prop["stable"].items()}),
            Workshop(**{unit: n_packs * amount for unit, amount in rec_prop["workshop"].items()}),
        )

        self.recruit(rec)

    def recruit(self, rec: Recruitment):
        for building, units in asdict(rec).items():
            if any(units.values()):
                self.go_to(building)
                self.driver.execute_script("window.scrollTo(0, 2000)")
                for unit, amount in units.items():
                    if amount > 0:
                        sleep_()
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, '#' + unit + '_0').send_keys(str(amount))
                        except Exception as e:
                            logging.warning("Cannot recruit %s" % unit)
                sleep_()
                self.driver.find_element(By.XPATH, "//input[@value='Rekrutacja']").click()
                logging.info('Recruited: %s' % str(units))

    def train_knight(self):
        self.go_to("statue")
        els = self.driver.find_elements(By.XPATH, '//*[@id="knight_actions"]/div/a[1][text()="Trening XP"]')
        if len(els) == 1:
            sleep_()
            els[0].click()
            try:
                sleep_()
                self.driver.find_element(
                    By.XPATH, '//*[@id="popup_box_knight_regimens"]/div/div[2]/div[6]/a[1][text()="Start"]'
                ).click()
                logging.info("Starting knight trening.")
            except Exception as e:
                logging.warning("Cannot start knight trening.")

    def do_weapon_research(
        self,
        unit_id: Union[int, str],
        building_id: Union[int, str]
    ):
        self.go_to("smith")
        try:
            if isinstance(unit_id, str):
                unit_id = int(unit_id)
            if isinstance(building_id, str):
                building_id = int(building_id)

            sleep_()
            self.driver.find_element(
                By.XPATH,
                '//*[@id="tech_list"]/table/tbody/tr[%d]/td[%d]' % (unit_id + 1, building_id) +\
                '/table/tbody/tr/td[2]/a[contains(text(), "Technologia")]'
            ).click()
            logging.info('Research for weapon of unit %d from building %d started.' % (unit_id, building_id))
            runned = True
        except Exception as e:
            runned = False
        return runned

    def build(self, building: str, save: Union[bool, int, str] = False):
        self.go_to("main")

        try:
            waiting_time = self.driver.find_element(
                By.XPATH,
                '//*[@id="main_buildrow_%s"]/td[5]' % building
            ).text
            
            sleep_()
            self.driver.find_element(
                By.XPATH,
                '//a[contains(text(), "Poziom") and contains(@id, "main_buildlink_%s")]' % building
            ).click()
            logging.info('Building of %s started and will last %s.' % (building, waiting_time))
            runned = True
        except Exception as e:
            logging.warning('Cannot build %s.' % building)
            runned = False
            if isinstance(save, bool) and save is True\
                    or isinstance(save, str) and save == "True"\
                    or save.isnumeric() and int(save) != 0:
                self.set_fundraise(
                    *self._get_building_cost(building), cmd=['build', building, save]
                )
        return runned

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
        return int(wood), int(stone), int(iron)

    def set_fundraise(self, wood: int, stone: int, iron: int, cmd: List[str]):
        self.fundraise_cmd = cmd
        self.fundraise = [wood, stone, iron]
        logging.info(
            "Set fundraise: wood %d, stone %d, iron %d." % (wood, stone, iron)
        )

    def unset_fundraise(self):
        self.fundraise_cmd = []
        self.fundraise = [0, 0, 0]
        logging.info("Fundraise unset.")

    def run_cmd(self, cmd: List[str]) -> bool:
        try:
            func = getattr(self, cmd[0])
            runned = func(*cmd[1:])
            if runned and self.compare_cmds(self.fundraise_cmd, cmd):
                self.unset_fundraise()
        except Exception as e:
            runned = None
        
        self.log_priority_run(runned, cmd)
        return runned

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

    def go_to(self, screen: str, mode: str = None):
        sleep_()
        url = self.current_village_url.replace('overview', screen)
        self.driver.get(url)
        if mode is not None:
            sleep_()
            url += "&mode=" + mode
            self.driver.get(url)
        
            els = self.driver.find_elements(By.XPATH, '//div[@class="content" and text()="Niewłaściwy tryb"]')
            if len(els) > 0:
                logging.error("Invalid mode \"%s\". Url: %s." % (mode, url))

    def setup_next_visit_time(self, delta: timedelta, additional_minutes: int = 0):
        self.next_visit_time = datetime.now() + delta + timedelta(minutes=additional_minutes)

    def quit_session(self):
        sleep_(2)
        self.driver.quit()
        logging.info("Driver quited session.")

    def wait(self):
        if self.loop and datetime.now() <= self.next_visit_time:
            logging.info("Waiting until %s." % self.next_visit_time.strftime("%Y-%m-%d, %H:%M:%S"))
            pause.until(self.next_visit_time)

    def run_cycle(self, tactic: Callable, *args):
        self.init_driver()
        self.login(world_nr=175)
        tactic(*args)
        self.quit_session()
        self.wait()

    def tactic1(self):
        self.run_priorities()
        self.train_knight()
        self.scavenge(knight=False)
        self.recruit_proportionally(path="recruit_proportions.json")

    def tactic2(self):
        self.run_priorities(n=2)
        self.train_knight()
        self.scavenge(knight=False)
        # self.recruit_proportionally(path="recruit_proportions.json")

    def log_error(self):
        logging.error("Error! [x]")
        if self.driver is not None:
            self.driver.save_screenshot("screenshot.png")
            logging.error("Screenshot took.")

    def quit_run(self):
        if self.driver is not None:
            self.quit_session()
        logging.info("Bot ends.")

    def run(self):
        logging.info("====== New session ======")
        try:
            while True:
                self.run_cycle(self.tactic2)
        except Exception as e:
            self.log_error()
            raise e
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt.")
        finally:
            self.quit_run()

if __name__ == "__main__":
    sc_bot = Scavenging()
    sc_bot.run()
