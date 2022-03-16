from dataclasses import asdict, fields
import logging
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from typing import List, Union

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Recruitment, Barracks, Stable, Workshop, Cost


class Recruit(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)

    def _load_costs(self, path: Path = Path("data/costs.json")) -> List[Cost]:
        with open(path) as file:
            costs = json.loads(file.read())
        costs = {unit: Cost(**cost) for unit, cost in costs.items()}
        return costs

    def _load_recruitment_proportions(
        self, path: Path = Path("data/recruit_proportions.json")
    ) -> Recruitment:
        with open(path) as file:
            rp = json.loads(file.read())
        rp = Recruitment(
            Barracks(**rp["barracks"]),
            Stable(**rp["stable"]),
            Workshop(**rp["workshop"])
        )
        return rp
        
    def _count_requirements(self, rp: Recruitment, costs: List[Cost]) -> Cost:
        req = Cost()
        for building in fields(rp):
            units = getattr(rp, building.name)
            for unit in fields(units):
                proportion = getattr(units, unit.name)

                req.wood += costs[unit].wood * proportion
                req.stone += costs[unit].stone * proportion
                req.iron += costs[unit].iron * proportion
        return req

    def _get_max_packs(self, rp: Recruitment, costs: List[Cost]):        
        req = self._count_requirements(rp, costs)
        wood, stone, iron = self.get_resources()

        n_packs = int(min([
            wood / req.wood, stone / req.stone, iron / req.iron
        ]))
        return n_packs

    def _proportions_to_recruitment(self, rp: Recruitment, n_packs: int) -> Recruitment:
        for building in fields(rp):
            units = getattr(rp, building.name)
            for unit in fields(units):
                amount = getattr(units, unit.name)
                setattr(units, unit.name, n_packs * amount)
        return rp

    def run(
        self, path: Path = Path("data/recruit_proportions.json")
    ):
        rp = self._load_recruitment_proportions(path)
        costs = self._load_costs()

        n_packs = self._get_max_packs(rp, costs)
        rec = self._proportions_to_recruitment(rp, n_packs)

        self.recruit(rec)

    def recruit(self, rec: Recruitment):
        if self._building_is_needed(rec.barracks):
            self.recruit_in_building(rec.barracks, "barracks")
        if self._building_is_needed(rec.stable):
            self.recruit_in_building(rec.stable, "stable")
        if self._building_is_needed(rec.workshop):
            self.recruit_in_building(rec.workshop, "workshop")

    def _building_is_needed(self, units: Union[Barracks, Stable, Workshop]):
        res = False
        for unit in fields(units):
            if getattr(units, unit.name) > 0:
                res = True
                break
        return res

    def recruit_in_building(self, units: Union[Barracks, Stable, Workshop], building_name: str):
        self.go_to(building_name)
        self.driver.execute_script("window.scrollTo(0, 2000)")
        for unit, amount in units.items():
            if amount > 0:
                self._write_unit_number(unit, amount)
        self.sleep()
        self.driver.find_element(By.XPATH, "//input[@value='Rekrutacja']").click()
        logging.info('Recruited: %s' % str(units))

    def _write_unit_number(self, unit: str, amount: int):
        self.sleep()
        try:
            self.driver.find_element(By.CSS_SELECTOR, '#' + unit + '_0').send_keys(str(amount))
        except Exception as e:
            logging.warning("Cannot recruit %s" % unit)
