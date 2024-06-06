import asyncio
from queue import Queue
from pixel.variables import CommonVariables, VariablesNames
from pixel.web.specification import SpecGenerator
import pixel.web.web as web
import pixel.cli.executor as executor
import sys
import os
from pathlib import Path
import atexit
import shutil
import matplotlib
from swagger_ui import tornado_api_doc

async def main():
    init()
    atexit.register(exit_hook)
    if CommonVariables.get_var(VariablesNames.RUNNER_TO_APP_QUEUE).get() == executor.ScriptEvent.STARTED:
        app = await web.main()
        swagger(app)
        SpecGenerator().generate()
        await asyncio.Event().wait()
    else:
        print("Failed to start app")

def swagger(app):
    tornado_api_doc(app, config_path=CommonVariables.get_var(VariablesNames.SPEC_PATH), url_prefix='/docs', title='Docs')

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
    CommonVariables.set_var(VariablesNames.TITLE, "Pixel App")
    CommonVariables.set_var(VariablesNames.SCRIPT_NAME, script_name)
    CommonVariables.set_var(VariablesNames.SPEC_PATH, os.path.join(os.path.dirname(__file__), "openapi.json"))
    # INITIALIZING THINGS
    appToRunner = Queue()
    runnerToApp = Queue()
    runner = executor.ScriptRunner(appToRunner, runnerToApp)
    runner.daemon = True
    runner.start()
    appToRunner.put_nowait(executor.ScriptEvent.START)
    matplotlib.use("agg")

    CommonVariables.set_var(VariablesNames.EVENT_QUEUE, appToRunner)
    CommonVariables.set_var(VariablesNames.RUNNER_TO_APP_QUEUE, runnerToApp)


def exit_hook():
    path = CommonVariables.get_var(VariablesNames.STATIC_PATH)
    shutil.rmtree(path, ignore_errors=True)
    print("Removed directory")
