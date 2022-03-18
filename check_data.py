import csv
import json
from multiprocessing.sharedctypes import Value
from pathlib import Path

from data_types import Scavengers
from tactics import RecruitTactic, ScavengeTactic, TrainTactic


def file_exists(path: Path):
    assert path.is_file(), 'Cannot find file "%s".' % str(path)


def check_build_to_prevent(
    path: Path = Path('data/build_to_prevent.json')
):
    file_exists(path)
    with open(path, "r") as file:
        prior = json.load(file)

    def check_attribute(atr: str):
        assert atr in prior, 'Attribute "%s" not found.' % atr
        assert isinstance(prior[atr], bool), 'Value "%s" should be boolean.' % prior[atr]

    check_attribute("farm")
    check_attribute("farm_in_process")
    check_attribute("storage")
    check_attribute("storage_in_process")
    return True


def check_build(
    path: Path = Path('data/build.csv')
):
    file_exists(path)
    with open(path, "r") as file:
        commissions = list(csv.reader(file))
    for com_nr, com in enumerate(commissions):
        assert len(com) == 2, 'Wrong number of arguments in line %d' % com_nr
        building, fundraise = com
        assert building in [
            "main", "barracks", "stable", "garage", "smith", "statue", "market",
            "wood", "stone", "iron", "farm", "storage", "hide", "wall", "snob"
        ], 'Unknown building "%s" in line %d.' % (building, com_nr)
        assert fundraise in [True, False, "True", "False", 1, 0, "1", "0"],\
            'Unknown fundraise state "%s" in line %d.' % (fundraise, com_nr)
    return True


def check_recruit(
    path: Path = Path('data/recruit.json')
):
    file_exists(path)
    try:
        with open(path, "r") as file:
            rtp = json.load(file)
        RecruitTactic(**rtp)
    except:
        raise ValueError("Bad recruit.json tactic file.")
    return True


def check_recruit_to_prevent(
    path: Path = Path('data/recruit_to_prevent.json')
):
    try:
        if path.is_file():
            with open(path, "r") as file:
                rtp = json.load(file)
            RecruitTactic(**rtp)
    except:
        raise ValueError("Bad recruit_to_prevent.json tactic file.")
    return True


def check_costs(
    path: Path = Path('data/costs.json')
):
    file_exists(path)

    def check_resource(atr: str, cost: dict):
        assert atr in cost, 'Attribute "%s" not found in cost.'
        assert isinstance(cost[atr], int), 'Cost should be integer.'
        assert cost[atr] > 0, 'Cost should be positive.'

    with open(path, "r") as file:
        costs = json.load(file)
    for unit, cost in costs.items():
        assert unit in [
            "spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult"
        ], 'Unknown unit "%s".' % unit
        check_resource("wood", cost)
        check_resource("stone", cost)
        check_resource("iron", cost)
    return True


def check_scavenge(
    path: Path = Path("data/scavenge.json")
):
    file_exists(path)
    try:
        with open(path, "r") as file:
            tactic = json.load(file)
        tactic = ScavengeTactic(
            divide=tactic["divide"],
            lvls=tactic["lvls"],
            except_=Scavengers(**tactic.get("except_", {})),
            troops_lvl1=Scavengers(**tactic.get("lvl1", {})),
            troops_lvl2=Scavengers(**tactic.get("lvl2", {})),
            troops_lvl3=Scavengers(**tactic.get("lvl3", {})),
            troops_lvl4=Scavengers(**tactic.get("lvl4", {}))
        )
    except Exception as e:
        raise ValueError("Bad scavenge.json tactic file.")


def check_train(path: Path = Path('data/train.json')):
    file_exists(path)
    with open(path, "r") as file:
        tactic = json.load(file)
    try:
        TrainTactic(**tactic)
    except Exception as e:
        raise ValueError("Bad train.json tactic file.")


def check_all_files():
    check_build_to_prevent()
    check_build()
    check_recruit()
    check_recruit_to_prevent()
    check_costs()
    check_scavenge()
    check_train()


if __name__ == '__main__':
    check_all_files()
    print("Files are OK.")
