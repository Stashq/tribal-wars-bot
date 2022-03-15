from dataclasses import dataclass, fields


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

@dataclass
class Scavengers:
    spear: int = 0
    sword: int = 0
    axe: int = 0
    arch: int = 0
    light: int = 0
    marcher: int = 0
    heavy: int = 0
    knight: int = 0

    def __eq__(self, other):
        result = True
        for unit in fields(self):
            this_val = getattr(self, unit.name)
            other_val = getattr(other, unit.name)
            if this_val != other_val:
                result = False
                break
        return result

@dataclass
class Cost:
    wood: int = 0
    stone: int = 0
    iron: int = 0