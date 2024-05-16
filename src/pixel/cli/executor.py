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
            event = self.queue.get()
            try:
                self.lock.acquire()
                if event == ScriptEvent.START:
                    self.executeInitial()
                elif event == ScriptEvent.RERUN:
                    self.executeRerun()
            except Exception as e:
                print(e)
            finally:
                self.lock.release()

    def executeInitial(self):
        _execute_script()
        observerInstance.reloadObserver()
        gc.collect()

    def executeRerun(self):
        wmSnapshot = defaultWidgetManager.snapshot()
        _execute_script()
        observerInstance.reloadObserver()

        diffChecker = DiffChecker(wmSnapshot)
        defaultWidgetManager.executed()
        defaultWidgetManager.cleanup()
        if diffChecker.hasDiff:
            cb = lambda: defaultWidgetManager.sendDiff(diffChecker.diff)
            TornadoIOLoop.var.addCallback(cb)

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
