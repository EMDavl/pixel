from queue import Queue
from pixel.variables import CommonVariables, VariablesNames
import pixel.web.web as web
import pixel.cli.executor as executor
import sys
import os
from pathlib import Path
import atexit
import shutil
import matplotlib


async def main():
    init()
    atexit.register(exit_hook)
    queue = Queue()
    runner = executor.ScriptRunner(queue)
    runner.daemon = True
    runner.start()
    CommonVariables.set_var(VariablesNames.EVENT_QUEUE, queue)
    queue.put_nowait(executor.ScriptEvent.START)
    await web.main()


def init():
    """
    Responsible for initialization of necessary objects:
     - singletons
     - folders
     - ...
    """

    # CREATING FOLDER FOR GENERATED CONTENT
    script_name = sys.argv[1]
    path = Path(os.path.join(os.path.dirname(script_name), ".static"))
    if path.exists:
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir()

    # SETTING SOME COMMON VARIABLES
    CommonVariables.set_var(VariablesNames.STATIC_PATH, path)
    CommonVariables.set_var(VariablesNames.SCRIPT_NAME, script_name)

    # INITIALIZING THINGS
    matplotlib.use("agg")


def exit_hook():
    path = CommonVariables.get_var(VariablesNames.STATIC_PATH)
    shutil.rmtree(path, ignore_errors=True)
    print("Removed directory")
