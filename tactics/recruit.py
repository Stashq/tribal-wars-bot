from dataclasses import dataclass, asdict
from datetime import timedelta, datetime
import json
from pathlib import Path

from data_types import Cost, Recruitment


@dataclass
class RecruitTactic:
    recruitment: Recruitment
    run: bool = True
    type_: str = "values"
    savings: Cost = Cost()
    limits: Cost = Cost()
    time_delta: timedelta = None

    def __post_init__(self):
        assert self.type_ in ["values", "proportions"]

        if self.run is True or self.run == "True" or self.run == "1":
            self.run = True
        else:
            self.run = False

        if isinstance(self.time_delta, str):
            td = datetime.strptime(self.time_delta, "%H:%M:%S")
            self.time_delta = timedelta(
                hours=td.hour, minutes=td.minute, seconds=td.second)

        if isinstance(self.recruitment, dict):
            self.recruitment = Recruitment(**self.recruitment)
        if isinstance(self.savings, dict):
            self.savings = Cost(**self.savings)
        if isinstance(self.limits, dict):
            self.limits = Cost(**self.limits)

    def to_json(
        self,
        path: Path = Path(
            "data/recruit_to_prevent.json")
    ):
        # self.time_delta = datetime.strftime(
        #     self.time_delta, "%H:%M:%S"
        # )
        with open(path, "w") as file:
            json.dump(asdict(self), file)
