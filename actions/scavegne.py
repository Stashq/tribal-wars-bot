from actions.base import Action
from actions.action_input import ActionInput
from tactics.scavegne import ScavegneTactic


class Scavegne(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.go_to(screen="place", mode="scavenge")

    def parse_tactic(self, tactic: ScavegneTactic):
        tactic.

    def _check_availibility(self):
        pass

    def run(self, tactic: ScavegneTactic):
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