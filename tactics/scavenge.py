from dataclasses import dataclass, fields, replace, field
import logging
from typing import List, Tuple, Dict

from data_types import Scavengers


@dataclass
class ScavengeTactic:
    run: bool = True
    divide: bool = False
    lvls: list = field(default_factory=lambda: [2, 3, 4])
    except_: Scavengers = Scavengers()
    troops_lvl1: Scavengers = Scavengers()
    troops_lvl2: Scavengers = Scavengers()
    troops_lvl3: Scavengers = Scavengers()
    troops_lvl4: Scavengers = Scavengers()

    def __post_init__(self):
        for unit in fields(Scavengers):
            value = getattr(self.except_, unit.name)
            assert isinstance(value, int) or value == "all"

        assert isinstance(self.divide, bool)

        if self.lvls is None:
            self.lvls = [2, 3, 4]

        if not self.divide:
            for troops in [self.troops_lvl1, self.troops_lvl2, self.troops_lvl3, self.troops_lvl4]:
                assert not self._troops_are_empty(troops)

    def get_troops_per_lvl(
        self,
        available_troops: Scavengers,
        transported_troops: Scavengers
    ) -> Dict[int, Scavengers]:
        available_troops = self._subtract_troops(available_troops, transported_troops, self.except_)[0]
        if len(self.lvls) == 0:
            result = {}
        elif self.divide:
            result = self._devide_troops(
                available_troops, divisions=len(self.lvls))
        else:
            result = self._adjust_troops_per_lvl(
                available_troops, self.lvls)
        return result

    def _subtract_troops(
        self,
        available_troops: Scavengers,
        transported_troops: Scavengers,
        subtrahend: Scavengers
    ) -> Tuple[Scavengers]:
        result = Scavengers()
        real_subtrahend = Scavengers()
        for unit in fields(Scavengers):
            sub = getattr(subtrahend, unit.name)
            available = getattr(available_troops, unit.name)
            trans = getattr(transported_troops, unit.name)

            if sub == "all":
                res = 0
            elif sub < trans:
                res = available
            else:
                res = available + trans - sub
                if res < 0:
                    res = 0

            setattr(result, unit.name, res)
            setattr(real_subtrahend, unit.name, available - res)
        return result, real_subtrahend

    def _adjust_troops_per_lvl(self, troops: Scavengers, lvls: List[int]) -> Dict[int, Scavengers]:
        available_troops = replace(troops)
        troops_per_lvl = [self.troops_lvl1, self.troops_lvl2, self.troops_lvl3, self.troops_lvl4]
        result = {}
        for lvl in reversed(lvls):
            current_troops = troops_per_lvl[lvl - 1]
            available_troops, adjusted_lvl_troops = self._subtract_troops(
                troops=available_troops, subtrahend=current_troops)
            result[lvl] = adjusted_lvl_troops
            if adjusted_lvl_troops != current_troops:
                self.log("Not enough troops for scavenging on lvl %d." % lvl, logging.WARN)
        return result

    def _troops_are_empty(self, troops: Scavengers) -> bool:
        empty = True
        for unit in fields(Scavengers):
            if getattr(troops, unit.name) > 0:
                empty = False
                break
        return empty

    def _devide_troops(self, troops: Scavengers, divisions: int) -> Dict[int, Scavengers]:
        package = self._count_package_troops(troops, divisions)
        last_package = self._count_last_lvl_troops(troops, package, divisions)
        result = {}
        for lvl in self.lvls:
            if lvl == max(self.lvls):
                result[lvl] = last_package
            else:
                result[lvl] = package
        return result

    def _count_package_troops(self, troops: Scavengers, divisions: int) -> Scavengers:
        result = Scavengers()
        for unit in fields(Scavengers):
            value = getattr(troops, unit.name)
            setattr(result, unit.name, int(value/divisions))
        return result

    def _count_last_lvl_troops(self, troops: Scavengers, troop_package: Scavengers, divisions: int) -> Scavengers:
        result = Scavengers()
        for unit in fields(Scavengers):
            trp_value = getattr(troops, unit.name)
            pack_value = getattr(troop_package, unit.name)
            res_value = trp_value - pack_value * (divisions - 1)
            setattr(result, unit.name, res_value)
        return result
