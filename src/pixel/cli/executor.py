from enum import Enum, auto
from tornado.ioloop import IOLoop
from pixel.cache.cache_manager import CacheManager
from pixel.variables import CommonVariables, VariablesNames
from threading import Lock, Thread
import gc
from pixel.observer.observer import observer_instance
from pixel.web.specification import SpecGenerator
from pixel.web.web import TornadoIOLoop
from pixel.widget_manager.widget_manager import defaultWidgetManager, WidgetManagerDiffChecker
from queue import Queue
from pixel.web.processors import defaultProcessorManager

import traceback


class ScriptEvent(Enum):
    START = auto()
    STARTED = auto()
    RERUN = auto()
    FAILED = auto()


class ScriptRunner(Thread):
    def __init__(self, consume: Queue, produce: Queue) -> None:
        super().__init__()
        self.consume = consume
        self.produce = produce
        self.lock = Lock()
        self.lastExecutedBytecode = None

    def run(self) -> None:
        while True:
            event = self.consume.get()
            try:
                self.lock.acquire()
                if event == ScriptEvent.START:
                    self.executeInitial()
                elif event == ScriptEvent.RERUN:
                    self.executeRerun()
            except Exception:
                traceback.print_exc()
            finally:
                self.lock.release()

    def executeInitial(self):
        try:
            bytecode, _ = self.getByteCode()
            self._execute_script(bytecode)
            observer_instance.reloadObserver()
            gc.collect()
            self.produce.put(ScriptEvent.STARTED)
        except Exception:
            traceback.print_exc()
            self.produce.put(ScriptEvent.FAILED)

    def executeRerun(self):
        bytecode, needReexecute = self.getByteCode()
        if (not needReexecute):
            return
        
        wmSnapshot = defaultWidgetManager.snapshot()
        cmSnapshot = CacheManager.snapshot()
        procSnapshot = defaultProcessorManager.snapshot()

        try:
            self._execute_script(bytecode)
        except Exception as e:
            print("Failed to execute script. Rolling back")
            defaultWidgetManager.rollback()
            return
    
        observer_instance.reloadObserver()

        widgetManagerDiffChecker = WidgetManagerDiffChecker(wmSnapshot)
        CacheManager.cleanup(cmSnapshot)

        defaultWidgetManager.executed()
        defaultWidgetManager.cleanup(widgetManagerDiffChecker.resourceToBeDeleted)
        defaultProcessorManager.executed()
    
        if widgetManagerDiffChecker.hasDiff:
            print('found diff - adding callback')
            cb = lambda: defaultWidgetManager.sendDiff(widgetManagerDiffChecker.diff)
            TornadoIOLoop.var.addCallback(cb)
        
        if (procSnapshot.has_diff()):
            print("Regenerating specification")
            SpecGenerator().generate()

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
