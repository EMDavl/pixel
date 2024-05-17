from enum import Enum, auto
from tornado.ioloop import IOLoop
from pixel.variables import CommonVariables, VariablesNames
from threading import Lock, Thread
import gc
from pixel.observer.observer import observerInstance
from pixel.web.web import TornadoIOLoop
from pixel.widget_manager.widget_manager import defaultWidgetManager, DiffChecker
from queue import Queue

import traceback


class ScriptEvent(Enum):
    START = auto()
    RERUN = auto()


class ScriptRunner(Thread):
    def __init__(self, queue: Queue) -> None:
        super().__init__()
        self.queue = queue
        self.lock = Lock()
        self.lastExecutedBytecode = None

    def run(self) -> None:
        while True:
            event = self.queue.get()
            print('got event!')
            try:
                self.lock.acquire()
                if event == ScriptEvent.START:
                    self.executeInitial()
                elif event == ScriptEvent.RERUN:
                    self.executeRerun()
            except Exception as e:
                print("UPAL")
                print(e)
                traceback.print_exc()
            finally:
                print("released lock")
                self.lock.release()

    def executeInitial(self):
        bytecode, _ = self.getByteCode()
        self._execute_script(bytecode)
        observerInstance.reloadObserver()
        gc.collect()

    def executeRerun(self):
        bytecode, needReexecute = self.getByteCode()
        if (not needReexecute):
            print("not reexecuted")
            return
        print('reexecuted')
        wmSnapshot = defaultWidgetManager.snapshot()
        self._execute_script(bytecode)

        print("reloading observer")
        observerInstance.reloadObserver()

        print("checking for a diff")
        diffChecker = DiffChecker(wmSnapshot)
        defaultWidgetManager.executed()
        print('cleaning up')
        defaultWidgetManager.cleanup(diffChecker.resourceToBeDeleted)

        if diffChecker.hasDiff:
            print('found diff - adding callback')
            cb = lambda: defaultWidgetManager.sendDiff(diffChecker.diff)
            TornadoIOLoop.var.addCallback(cb)

        print('collecting garbage')
        gc.collect()

    def getByteCode(self):
        with open(CommonVariables.get_var(VariablesNames.SCRIPT_NAME)) as f:
            file = f.read()

        bytecode = compile(
            file,
            mode="exec",
            filename=CommonVariables.get_var(VariablesNames.SCRIPT_NAME),
        )

        return bytecode, bytecode != self.lastExecutedBytecode
    def _execute_script(self, bytecode): 
        exec(bytecode, globals())
        self.lastExecutedBytecode = bytecode
        return True
