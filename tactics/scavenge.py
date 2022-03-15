from dataclasses import dataclass, fields, replace
import logging
from typing import List, Tuple

from data_types import Scavengers


@dataclass
class ScavegneTactic:
    divide: int = None
    except_: Scavengers = Scavengers()
    lvl1: Scavengers = Scavengers()
    lvl2: Scavengers = Scavengers()
    lvl3: Scavengers = Scavengers()
    lvl4: Scavengers = Scavengers()

    def __post_init__(self):
        for unit in fields(Scavengers):
            value = getattr(self.except_, unit.name)
            assert isinstance(value, int) or value == "all"
        
        assert self.division is None\
            or isinstance(self.division, int) and self.divide in [0, 1]
        
        if self.divide is None or self.divide == 0:
            for lvl in [self.lvl1, self.lvl2, self.lvl3, self.lvl4]:
                assert not self._troops_are_empty(lvl)

    def get_lvls_troops(self, troops: Scavengers, available_lvls: List[int]) -> List[Scavengers]:
        troops = self._subtract_troops(troops, self.except_)[0]
        if self.divide == 1:
            result = self._devide_troops(troops, divisions=len(available_lvls))
        else:
            pass

    def _subtract_troops(self, troops: Scavengers, subtrahend: Scavengers) -> Tuple[Scavengers]:
        result = Scavengers()
        real_subtrahend = Scavengers()
        for unit in fields(Scavengers):
            sub_value = getattr(subtrahend, unit.name)
            trp_value = getattr(troops, unit.name)

            if sub_value == "all":
                res_value = 0
            else:
                res_value = trp_value - sub_value
                if res_value < 0:
                    res_value = 0

            setattr(result, unit.name, res_value)
            setattr(real_subtrahend, unit.name, trp_value - res_value)
        return result, real_subtrahend

    def _adjust_lvls(self, troops: Scavengers, available_lvls: List[int]) -> List[Scavengers]:
        available_troops = replace(troops)
        lvls = [self.lvl1, self.lvl2, self.lvl3, self.lvl4]
        result = []
        for av_lvl in reversed(available_lvls):
            current_troops = lvls[av_lvl - 1]
            available_troops, adjusted_lvl_troops = self._subtract_troops(
                troops=available_troops, subtrahend=current_troops)
            result += [adjusted_lvl_troops]
            if adjusted_lvl_troops != current_troops:
                logging.warning("Not enough troops for scavenging on lvl %d." % av_lvl)
        return result

    def _troops_are_empty(self, troops: Scavengers) -> bool:
        emptiness = True
        for unit in fields(Scavengers):
            if getattr(troops, unit.name) > 0:
                emptiness = False
                break
        return emptiness

    def _devide_troops(self, troops: Scavengers, divisions: int) -> List[Scavengers]:
        package = self._count_package_troops(troops, divisions)
        last_package = self._count_last_lvl_troops(troops, package, divisions)
        result = [package] * (divisions - 1) + [last_package]
        return result

    def _count_package_troops(self, troops: Scavengers, divisions: int) -> Scavengers:
        result = Scavengers()
        for unit in fields(Scavengers):
            value = getattr(troops, unit.name)
            setattr(result, unit, int(value/divisions))
        return result

    def _count_last_lvl_troops(self, troops: Scavengers, troop_package: Scavengers, divisions: int) -> Scavengers:
        result = Scavengers()
        for unit in fields(Scavengers):
            trp_value = getattr(troops, unit.name)
            pack_value = getattr(troop_package, unit.name)
            res_value = trp_value - pack_value * (divisions - 1)
            setattr(result, unit, res_value)
        return result
