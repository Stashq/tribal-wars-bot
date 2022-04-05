from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import inspect
import logging
import pause
from typing import Type, Tuple, Union, Dict, List

from actions import Action, Build, Farm, Recruit, Scavenge, Train


# name, waiting time, commission id (if exists)
Task = Tuple[str, timedelta, str]


@dataclass
class Scheduler:
    build: datetime = None
    farm: Dict[str, datetime] = None
    recruit: datetime = None
    scavenge: datetime = None
    train: datetime = None

    def get_earliest_task(self) -> Tuple[Type[Action], datetime, str]:
        final_task = (None, datetime.now() + timedelta(days=999), None)
        tasks = self._aggregate_tasks()

        for task in tasks:
            final_task = self._select_earlier(
                final_task, task
            )

        action_class = self._str_to_action(final_task[0])
        time_, com_id = final_task[1:3]
        return action_class, time_, com_id

    def _aggregate_tasks(self) -> List[Task]:
        tasks = []
        fields = asdict(self)
        for f_name, f_val in fields.items():
            if f_val is None:
                continue
            if isinstance(f_val, datetime):
                tasks += [(f_name, f_val, None)]
            elif isinstance(f_val, dict):
                time_, com_id = self._get_earliest_commission(f_val)
                tasks += [(f_name, time_, com_id)]
        return tasks

    def _select_earlier(
        self, task1: Task, task2: Task
    ) -> Task:
        if task1[1] < task2[1]:
            return task1
        else:
            return task2

    def _get_earliest_commission(self, commissions: Dict) -> Tuple[timedelta, str]:
        t = datetime.now() + timedelta(days=999)
        c_id = None
        for com_key, com_val in commissions.items():
            if t > com_val:
                t = com_val
                c_id = com_key
        return t, c_id

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

    def set_waiting_time(
        self,
        action: Action,
        action_res: Union[timedelta, Tuple[timedelta, str], Dict[str, timedelta]]
    ):
        cmd = self._action_to_str(action)
        if isinstance(action_res, datetime):
            setattr(self, cmd, action_res)
        elif isinstance(action_res, timedelta):
            time_ = datetime.now() + action_res
            setattr(self, cmd, time_)
        elif isinstance(action_res, Tuple):
            time_ = datetime.now() + action_res[0]
            coms = getattr(self, cmd)
            coms[action_res[1]] = time_
        elif isinstance(action_res, Dict):
            for com_id, td in action_res.items():
                action_res[com_id] = datetime.now() + td
            setattr(self, cmd, action_res)
        else:
            raise ValueError('Unknown type of action response: %s.' % str(action_res))

    def reset_waiting_time(self, action: Action):
        cmd = self._action_to_str(action)
        setattr(self, cmd, None)

    def wait(self) -> Tuple[Type[Action], str]:
        Action_, time_, com_id = self.get_earliest_task()
        logging.info("Waiting until %s." % time_.strftime("%Y-%m-%d, %H:%M:%S"))
        pause.until(time_)
        self.reset_waiting_time(Action_)
        return Action_, com_id

    def log_times(self, village_coordinates: str = ''):
        text = '(%s) saved times:' % village_coordinates
        for name, time_ in asdict(self).items():
            if isinstance(time_, dict):
                time_ = min(time_.values())
            text += '\n\t%s:' % name
            text += ' '*(10-len(name))
            if time_ is not None:
                text += datetime.strftime(time_, "%Y-%m-%d %H:%M:%S")
            else:
                text += "---------- --:--:--"
        logging.info(text)
