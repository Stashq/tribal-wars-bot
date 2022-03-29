from __future__ import annotations
from dataclasses import dataclass, fields


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
