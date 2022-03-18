from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import inspect
import logging
import pause
from typing import Type, Tuple, Union

from actions import Action, Build, Farm, Recruit, Scavenge, Train


@dataclass
class Scheduler:
    build: datetime = None
    farm: datetime = None
    recruit: datetime = None
    scavenge: datetime = None
    train: datetime = None

    def get_earliest_task(self) -> Tuple[datetime, Type[Action]]:
        earliest_time = datetime.now() + timedelta(days=999)
        earliest_task_name = None
        tasks = asdict(self)
        for name, time_ in tasks.items():
            if time_ is not None and earliest_time > time_:
                earliest_time = time_
                earliest_task_name = name
        action_class = self._str_to_action(earliest_task_name)
        return earliest_time, action_class

    def _str_to_action(self, cmd: str) -> Type[Action]:
        if cmd == "build":
            action_class = Build
        elif cmd == "farm":
            action_class = Farm
        elif cmd == "recruit":
            action_class = Recruit
        elif cmd == "scavenge":
            action_class = Scavenge
        elif cmd == "train":
            action_class = Train
        else:
            raise ValueError('Unknown action "%s"' % cmd)
        return action_class

    def set_waiting_time(self, time_: Union[datetime, timedelta], action: Action):
        if isinstance(time_, timedelta):
            time_ = datetime.now() + time_

        cmd = self._action_to_str(action)
        setattr(self, cmd, time_)

    def _action_to_str(self, action: Union[Action, Type[Action]]) -> str:
        if inspect.isclass(action):
            action_type = action
        else:
            action_type = type(action)
        if action_type == Build:
            cmd = "build"
        elif action_type == Farm:
            cmd = "farm"
        elif action_type == Recruit:
            cmd = "recruit"
        elif action_type == Scavenge:
            cmd = "scavenge"
        elif action_type == Train:
            cmd = "train"
        else:
            raise ValueError('Unknown action "%s"' % str(action_type))
        return cmd

    def reset_waiting_time(self, action: Action):
        cmd = self._action_to_str(action)
        setattr(self, cmd, None)

    def wait(self):
        time_, action = self.get_earliest_task()
        logging.info("Waiting until %s." % time_.strftime("%Y-%m-%d, %H:%M:%S"))
        pause.until(time_)
        self.reset_waiting_time(action)
        return action

    def log_times(self):
        text = "Times set to: "
        for name, time_ in asdict(self).items():
            text += name + " "
            if time_ is not None:
                text += datetime.strftime(time_, "%Y-%m-%d, %H:%M:%S") + ", "
            else:
                text += "None, "
        text = text[:-2]
        logging.info(text)
