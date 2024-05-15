from enum import Enum, auto
from tornado.ioloop import IOLoop
from pixel.variables import CommonVariables, VariablesNames
from threading import Lock, Thread
import gc
from pixel.observer.observer import observerInstance
from pixel.web.web import TornadoIOLoop
from pixel.widget_manager.widget_manager import defaultWidgetManager, DiffChecker
from queue import Queue


class ScriptEvent(Enum):
    START = auto()
    RERUN = auto()


class ScriptRunner(Thread):
    def __init__(self, queue: Queue) -> None:
        super().__init__()
        self.queue = queue
        self.lock = Lock()

    def run(self) -> None:
        while True:
            print('waiting for event')
            event = self.queue.get()
            print('Got event: ', event)
            try:
                self.lock.acquire()
                print('acquired lock')
                if event == ScriptEvent.START:
                    self.executeInitial()
                elif event == ScriptEvent.RERUN:
                    self.executeRerun()
            finally:
                self.lock.release()
                print('released lock')

    def executeInitial(self):
        print("Executing script")
        _execute_script()
        print("Reloading observer")
        observerInstance.reloadObserver()
        print("Collecting garbage")
        gc.collect()

    def executeRerun(self):
        wmSnapshot = defaultWidgetManager.snapshot()
        _execute_script()
        observerInstance.reloadObserver()

        defaultWidgetManager.executed()
        diffChecker = DiffChecker(wmSnapshot)
        if diffChecker.hasDiff:
            cb = lambda: defaultWidgetManager.sendDiff(diffChecker.diff)
            TornadoIOLoop.var.addCallback(cb)

        print("Collecting garbage")
        gc.collect()


def _execute_script():
    with open(CommonVariables.get_var(VariablesNames.SCRIPT_NAME)) as f:
        file = f.read()

    bytecode = compile(
        file,
        mode="exec",
        filename=CommonVariables.get_var(VariablesNames.SCRIPT_NAME),
    )
    exec(bytecode, globals())
