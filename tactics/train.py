from dataclasses import dataclass

from data_types import Cost


@dataclass
class TrainTactic:
    run: bool
    savings: Cost
    limits: Cost
    minutes_after_attempt: int

    def __post_init__(self):
        if isinstance(self.savings, dict):
            self.savings = Cost(**self.savings)
        if isinstance(self.limits, dict):
            self.limits = Cost(**self.limits)

        if not isinstance(self.run, bool):
            self.run = bool(self.run)
        if not isinstance(self.minutes_after_attempt, int):
            self.minutes_after_attempt = bool(self.minutes_after_attempt)
