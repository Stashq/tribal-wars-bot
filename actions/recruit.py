from dataclasses import fields, asdict
from datetime import timedelta
import logging
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from typing import List, Union

from actions.base import Action
from actions.action_input import ActionInput
from data_types import Recruitment, Barracks, Stable, Workshop, Cost
from tactics.recruit import RecruitTactic


class Recruit(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)
        self.path = self.base_path / 'recruit.json'
        self.lowering_recources_path = self.base_path / 'recruit_to_prevent.json'
        self.costs = self._load_costs()

    def _load_costs(self) -> List[Cost]:
        with open('data/costs.json', "r") as file:
            costs = json.load(file)
        costs = {unit: Cost(**cost) for unit, cost in costs.items()}
        return costs

    def _load_recruit_tactic(
        self, path: Path
    ) -> RecruitTactic:
        with open(path, "r") as file:
            rt = json.load(file)
        res = RecruitTactic(**rt)
        return res
        
    def _count_requirements(self, rp: Recruitment) -> Cost:
        req = Cost()
        for building in fields(rp):
            units = getattr(rp, building.name)
            for unit in fields(units):
                proportion = getattr(units, unit.name)

                req.wood += self.costs[unit.name].wood * proportion
                req.stone += self.costs[unit.name].stone * proportion
                req.iron += self.costs[unit.name].iron * proportion
        return req

    def _get_max_packs(self, rt: RecruitTactic):        
        req = self._count_requirements(rt.recruitment)
        resources = self.get_resources(deduct_fundraise=False)
        resources = self.limit_resources(resources, rt.savings, rt.limits)

        n_packs = int(min([
            resources.wood / req.wood,
            resources.stone / req.stone,
            resources.iron / req.iron
        ]))
        return n_packs

    def _scale_recruitment(self, rp: Recruitment, scale: Union[int, float]) -> Recruitment:
        for building in fields(rp):
            units = getattr(rp, building.name)
            for unit in fields(units):
                amount = getattr(units, unit.name)
                setattr(units, unit.name, int(scale * amount))
        return rp

    def _get_proportional_recruitment(
        self, rt: RecruitTactic
    ) -> Recruitment:
        n_packs = self._get_max_packs(rt)
        rec = self._scale_recruitment(rt.recruitment, scale=n_packs)
        return rec

    def _adjust_recruitment(self, rt: RecruitTactic):
        resources = self.get_resources(deduct_fundraise=False)
        resources = self.limit_resources(resources, rt.savings, rt.limits)
        
        cost = self._count_requirements(rt.recruitment)
        min_proportion = min([
            resources.wood / cost.wood,
            resources.stone / cost.stone,
            resources.iron / cost.iron
        ])
        if min_proportion < 0:
            res = self._scale_recruitment(
                rt.recruitment,
                scale=min_proportion
            )
        else:
            res = rt.recruitment
        return res

    def run(self) -> timedelta:
        if self.lowering_recources_path.is_file():
            rt = self._load_recruit_tactic(self.lowering_recources_path)
            self.recruit(rt)
            self.lowering_recources_path.unlink()  # removes file

        rt = self._load_recruit_tactic(self.path)
        self.recruit(rt)

        return rt.time_delta

    def _tactic_to_recruitment(self, rt: RecruitTactic) -> Recruitment:
        if rt.type_ == "proportions":
            rec = self._get_proportional_recruitment(rt)
        else:
            rec = self._adjust_recruitment(rt)
        return rec

    def recruit(self, rt: RecruitTactic):
        if rt.run:
            rec = self._tactic_to_recruitment(rt)
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
        for unit, amount in asdict(units).items():
            if amount > 0:
                self._write_unit_number(unit, amount)
        self.sleep()
        self.driver.find_element(By.XPATH, "//input[@value='Rekrutacja']").click()
        self.log('Recruited: %s' % str(units))

    def _write_unit_number(self, unit: str, amount: int):
        self.sleep()
        try:
            self.driver.find_element(By.CSS_SELECTOR, '#' + unit + '_0').send_keys(str(amount))
        except Exception as e:
            self.log("Cannot recruit %s" % unit, logging.WARN)

    def _get_waiting_time(self, recruit_tactic: RecruitTactic) -> timedelta:
        return recruit_tactic.next_time
