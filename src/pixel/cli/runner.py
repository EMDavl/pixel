from pixel.router.router import Router
from pixel.variables import CommonVariables, VariablesNames
import pixel.web.web as web
import pixel.cli.executor as executor
import sys
import os
from pathlib import Path
import atexit
import shutil

async def main():
    # Инициализируем все что надо
    # Выполняем пользовательский код
    # Поднимаем сервер Tornado
    # Пишем что готовы к обработке входящих запросов
    init()
    atexit.register(exit_hook)
    await executor.execute_script()
    await web.main()


def init():
    """
    Responsible for initialization of necessary objects:
     - singletons
     - folders
     - ...
    """
    script_name = sys.argv[1]
    path = Path(os.path.join(os.path.dirname(script_name), ".static"))
    path.mkdir()
    CommonVariables.set_var(VariablesNames.STATIC_PATH, path)
    CommonVariables.set_var(VariablesNames.SCRIPT_NAME, script_name)
    Router.create()

def exit_hook():
    path = CommonVariables.get_var(VariablesNames.STATIC_PATH)
    shutil.rmtree(path, ignore_errors=True)
    print("Removed directory")

def sendImages(router):
    data = router.data
    for elementId in data.keys():
        web.MainWebSocket.broadcast_img(data[elementId], elementId)

   