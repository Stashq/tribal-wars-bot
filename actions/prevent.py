import json
import logging
from pathlib import Path
from selenium.webdriver.common.by import By
from typing import Dict

from actions import Action, ActionInput
from data_types import Cost, Recruitment
from tactics import PreventTactic, RecruitTactic


class Prevent(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.path = Path('data/prevent.json')
        self.build_to_prevent_path = self.base_path / 'build_to_prevent.json'

    def run(self):
        overflow = dict(
            pop_current_label=self._resource_not_fit("pop_current_label"),
            wood=self._resource_not_fit("wood"),
            stone=self._resource_not_fit("stone"),
            iron=self._resource_not_fit("iron")
        )
        if not any(overflow.values()):
            pass
        elif overflow["pop_current_label"]:
            self._deal_with_overpopulation(overflow)
        else:
            self._deal_with_resources_overflow(overflow)
        return None

    def _deal_with_overpopulation(
        self, overflow: dict
    ):
        with open(self.build_to_prevent_path, "r") as file:
            build_order = json.load(file)
        if build_order['farm_in_process'] not in ["1", "True", 1, True]:
            build_order["farm"] = True

            text = "Overpopulation. Commission farm building at first."
            if any([overflow["wood"], overflow["stone"], overflow["iron"]])\
                    and build_order['storage_in_process'] not in ["1", "True", 1, True]:
                build_order["storage"] = True
                text = "Overpopulation and resources overflow. Commission storage at first and farm at second building."
            logging.warning(text)

            with open(self.build_to_prevent_path, "w") as file:
                json.dump(build_order, file)

    def _deal_with_resources_overflow(self, overflow: dict):
        pt = self._load_prevent_tactic()
        rec = self._select_recruitment(overflow, pt)
        size = int(self._get_storage_size() * pt.percentage / 100)
        rt = RecruitTactic(
            run=True, type_="proportions", limits=Cost(*[size]*3),
            recruitment=rec#, time_delta=timedelta
        )
        rt.to_json(self.base_path / 'recruit_to_prevent.json')
        logging.warning("Resources overflow. Recruit commissioned.")

    def _select_recruitment(self, overflow: Dict[str, bool], pt: PreventTactic) -> Recruitment:
        if overflow["wood"] and overflow["stone"] and overflow["iron"]:
            res = pt.wood_and_stone_and_iron
        elif overflow["wood"] and overflow["stone"]:
            res = pt.wood_and_stone
        elif overflow["wood"] and overflow["iron"]:
            res = pt.wood_and_iron
        elif overflow["stone"] and overflow["iron"]:
            res = pt.stone_and_iron
        elif overflow["wood"]:
            res = pt.wood
        elif overflow["stone"]:
            res = pt.stone
        elif overflow["iron"]:
            res = pt.iron
        return res

    def _load_prevent_tactic(self):
        with open(self.path, "r") as file:
            prevention = json.load(file)
        pt = PreventTactic(**prevention)
        return pt

    def _resource_not_fit(self, id_: str):
        el = self.driver.find_element(
            By.XPATH, '//*[@id="%s"]' % id_)
        type_ = el.get_attribute("class")
        if type_ == "res" or type_ == '':
            res = False
        elif type_ == "warn_90":
            logging.warning('Resource with ID "%s" exceed 90%%.' % id_)
            res = True
        elif type_ == "warn":
            logging.warning('No space for resource with ID "%s".' % id_)
            res = True
        return res

    def _get_waiting_time(self):
        return None
