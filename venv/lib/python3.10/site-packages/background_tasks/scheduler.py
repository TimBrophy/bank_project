from dataclasses import dataclass
from typing import Callable, Union, NoReturn, Literal
from datetime import timedelta, datetime
from threading import Thread
from multiprocessing import Process
import time


@dataclass
class Task:
    func: Callable
    every: timedelta


def convert_to_deltatime(every: Union[timedelta, float, int]) -> timedelta:
    if isinstance(every, (float, int)):
        every = timedelta(seconds=every)

    return every


class Scheduler:
    _tasks: list[Task]

    def __init__(self):
        self._tasks = []

    def task(self, every: Union[timedelta, float, int]):
        def wrapper(func: Callable):
            self.add_task(func, every)
        return wrapper

    def add_task(self, func: Callable, every: Union[timedelta, float, int]):
        every = convert_to_deltatime(every)

        self._tasks.append(Task(
            func=func,
            every=every
        ))

    def run_as_threads(self):
        for task in self._tasks:
            Thread(
                target=run_task,
                args=(task,),
                daemon=True,
            ).start()

    def run_as_processes(self):
        for task in self._tasks:
            Process(
                target=run_task,
                args=(task,),
                daemon=True,
            ).start()

    def run_as_blocking(self) -> NoReturn:
        task_run_times = [(datetime.now(), task) for task in self._tasks]

        while True:
            for x in range(len(task_run_times)):
                last_ran, task = task_run_times[x]
                time_since = datetime.now() - last_ran
                if time_since >= task.every:
                    task.func()
                    task_run_times[x] = (datetime.now(), task)


def run_task(task: Task):
    while True:
        task.func()
        time.sleep(task.every.total_seconds())
