from __future__ import annotations
from dataclasses import dataclass, fields, asdict


@dataclass
class Barracks:
    spear: int = 0
    sword: int = 0
    axe: int = 0
    archer: int = 0

@dataclass
class Stable:
    spy: int = 0
    light: int = 0
    marcher: int = 0
    heavy: int = 0

@dataclass
class Workshop:
    ram: int = 0
    catapult: int = 0

@dataclass
class Recruitment:
    barracks: Barracks = Barracks()
    stable: Stable = Stable()
    workshop: Workshop = Workshop()

    def __post_init__(self):
        if self.barracks is None:
            self.barracks = Barracks()
        elif isinstance(self.barracks, dict):
            self.barracks = Barracks(**self.barracks)

        if self.stable is None:
            self.stable = Stable()
        elif isinstance(self.stable, dict):
            self.stable = Stable(**self.stable)

        if self.workshop is None:
            self.workshop = Workshop()
        elif isinstance(self.workshop, dict):
            self.workshop = Workshop(**self.workshop)

    def is_empty(self):
        for building_field in fields(self):
            building = getattr(self, building_field.name)
            for unit_field in fields(building):
                val = getattr(self, unit_field.name)
                if val != 0:
                    return False
        return True

    def limit(self, limit_: Recruitment):
        limited = asdict(Recruitment())
        rec = asdict(self)
        limit_ = asdict(limit_)

        for building in rec:
            for unit in rec[building]:
                if rec[building][unit] < limit_[building][unit]:
                    limited[building][unit] = rec[building][unit]
                else:
                    limited[building][unit] = limit_[building][unit]
        limited = Recruitment(**limited)
        return limited

@dataclass
class Scavengers:
    spear: int = 0
    sword: int = 0
    axe: int = 0
    archer: int = 0
    light: int = 0
    marcher: int = 0
    heavy: int = 0
    knight: int = 0

    def __eq__(self, other):
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            other_val = getattr(other, unit.name)
            if this_val != other_val:
                return False
        return True

    def is_empty(self):
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            if this_val != 0:
                return False
        return True


@dataclass
class Troops:
    spear: int = 0
    sword: int = 0
    axe: int = 0
    archer: int = 0
    spy: int = 0
    light: int = 0
    marcher: int = 0
    heavy: int = 0
    ram: int = 0
    catapult: int = 0
    knight: int = 0
    snob: int = 0

    def __eq__(self, other) -> bool:
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            other_val = getattr(other, unit.name)
            if this_val != other_val:
                return False
        return True

    def __le__(self, other: Troops) -> bool:
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            other_val = getattr(other, unit.name)
            if this_val > other_val:
                return False
        return True
        

    def is_empty(self) -> bool:
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            if this_val != 0:
                return False
        return True

    def limit(self, limit_: Troops) -> Troops:
        limited = asdict(Troops())
        rec = asdict(self)
        limit_ = asdict(limit_)

        for unit in rec:
            if rec[unit] < limit_[unit]:
                limited[unit] = rec[unit]
            else:
                limited[unit] = limit_[unit]
        limited = Troops(**limited)
        return limited

    def subtract(self, subtrahend: Troops) -> Troops:
        res = Troops()
        for unit in fields(self):
            val = getattr(self, unit.name) - getattr(subtrahend, unit.name)
            if val < 0:
                val = 0
            setattr(res, unit.name, val)
        return res


@dataclass
class Cost:
    wood: int = 0
    stone: int = 0
    iron: int = 0

    def all_less(self, cost2: Cost):
        return (
            self.wood < cost2.wood\
                and self.stone < cost2.stone\
                and self.iron < cost2.iron)

    def all_greater(self, cost2: Cost):
        return (
            self.wood > cost2.wood\
                and self.stone > cost2.stone\
                and self.iron > cost2.iron)
