from dataclasses import dataclass, asdict
from datetime import timedelta, datetime
import json
from pathlib import Path
from typing import List

from data_types import Troops


@dataclass
class FarmCommission:
    id_: str
    x: int
    y: int
    troops: Troops
    next_attempt: timedelta = None
    max_time: timedelta = None
    send_incomplete: bool = False

    def __post_init__(self):
        if isinstance(self.next_attempt, str):
            td = datetime.strptime(self.next_attempt, "%H:%M:%S")
            self.next_attempt = timedelta(
                hours=td.hour, minutes=td.minute, seconds=td.second)
        if isinstance(self.max_time, str):
            td = datetime.strptime(self.max_time, "%H:%M:%S")
            self.max_time = timedelta(
                hours=td.hour, minutes=td.minute, seconds=td.second)
        if isinstance(self.troops, dict):
            self.troops = Troops(**self.troops)

        assert isinstance(self.troops, Troops),\
            'Troops of farm commission should be Troops type or dictionary.'
        assert isinstance(self.id_, str),\
            'Attribute id_ of farm commission should be string.'
        assert isinstance(self.x, int),\
            'X coordinate of farm commission should be int.'
        assert isinstance(self.y, int),\
            'Y coordinate of farm commission should be int.'
        assert self.next_attempt is None or isinstance(self.next_attempt, timedelta),\
            'Next attempt of farm commission should be timedelta type.'
        assert self.max_time is None or isinstance(self.max_time, timedelta),\
            'Max time of farm commission should be timedelta type.'
        assert isinstance(self.send_incomplete, bool),\
            'Attribute send_incomplete of farm commission should be boolean type.'


@dataclass
class FarmTactic:
    commissions: List[FarmCommission]
    except_: Troops = Troops()
    run: bool = True

    def __post_init__(self):
        for i in range(len(self.commissions)):
            if isinstance(self.commissions[i], dict):
                self.commissions[i] = FarmCommission(
                    **self.commissions[i]
                )
            assert isinstance(self.commissions[i], FarmCommission),\
                'Commission number %d of farm tactic should be FarmCommission type.' % i
        
        ids = [com.id_ for com in self.commissions]
        assert len(ids) == len(set(ids)),\
            'Same id_ for farm commissions are not allowed.'

        if isinstance(self.except_, dict):
            self.except_ = Troops(
                **self.except_
            )
        assert isinstance(self.except_, Troops),\
            'Attribute except_ of farm tactic should be Troops type.'

        assert isinstance(self.run, bool),\
            'Run of farm tactic should be boolean type.'

    def to_json(
        self,
        path: Path = Path(
            "data/farm.json")
    ):
        with open(path, "w") as file:
            json.dump(asdict(self), file)
