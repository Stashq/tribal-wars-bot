from datetime import timedelta

from actions.base import Action
from actions.action_input import ActionInput


class Farm(Action):
    def __init__(self, input_: ActionInput):
        super().__init__(input_)

    def run(self):
        return None

    def _get_waiting_time(self) -> timedelta:
        return None
