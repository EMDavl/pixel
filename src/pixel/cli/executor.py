from tornado.ioloop import IOLoop
from pixel.variables import CommonVariables, VariablesNames
from threading import Thread
import gc
from pixel.observer.observer import observerInstance
from pixel.web.web import TornadoIOLoop
from pixel.widget_manager.widget_manager import defaultWidgetManager, DiffChecker


# TODO Как то сделать чтобы только один поток в единицу времени мог выполнять скрипт
class ScriptExecutor(Thread):

    def run(self) -> None:
        print("Executing script")
        _execute_script()
        print("Reloading observer")
        observerInstance.reloadObserver()
        print("Collecting garbage")
        gc.collect()

class ScriptRerunner(Thread):
    restarted = False
    def run(self):
        if ScriptRerunner.restarted:
            return
        ScriptRerunner.restarted = True
        wmSnapshot = defaultWidgetManager.snapshot()

        print("Executing script")
        _execute_script()
        print("Reloading observer")
        observerInstance.reloadObserver()

        defaultWidgetManager.executed()
        diffChecker = DiffChecker(wmSnapshot)
        print(diffChecker.hasDiff)
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

