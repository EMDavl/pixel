from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import os
import sys
from pixel.variables import CommonVariables, VariablesNames
from pixel.commons import Singleton


class ScriptModificationHandler(FileSystemEventHandler):
    def __init__(self, path_to_script, dependencies) -> None:
        super().__init__()
        self._scriptPath = path_to_script
        self._dependencies = dependencies
        print(self._dependencies)

    def on_modified(self, event: FileSystemEvent) -> None:
        # To prevent circular dependencies
        from pixel.cli.executor import ScriptRerunner
        if event.is_directory:
            return
        path = os.path.abspath(event.src_path)
        if path == self._scriptPath or path in self._dependencies:
            print("File {} has changed, reloading script".format(path))
            executor = ScriptRerunner()
            executor.start()
            

class ScriptModificationObserver(metaclass=Singleton):

    def __init__(self):
        self.obs = Observer()
        self.obs.start()
        self._watches = set()

    def reloadObserver(self):
        for watch in self._watches:
            self.obs.unschedule(watch)
        scriptName = CommonVariables.get_var(VariablesNames.SCRIPT_NAME)
        scriptDir = os.path.abspath(os.path.dirname(scriptName))
        scriptPath = os.path.abspath(scriptName)
        dependencies = self.getDependencies(scriptDir)
        eventHandler = ScriptModificationHandler(scriptPath, dependencies)
        self._watches.add(self.obs.schedule(eventHandler, scriptDir, True))

    def getDependencies(self, scriptDir):
        paths_extractors = [
            lambda m: [m.__file__],
            lambda m: [m.__spec__.origin],
            lambda m: [p for p in m.__path__._path],
        ]

        all_paths = set()
        for _, val in dict(sys.modules).items():
            for extract_paths in paths_extractors:
                potential_paths = []
                try:
                    potential_paths = extract_paths(val)
                except AttributeError:
                    pass
                all_paths.update(
                    [
                        os.path.abspath(str(p))
                        for p in potential_paths
                        if self.isValidFile(p, scriptDir)
                    ]
                )
        return all_paths

    def isValidFile(self, path, scriptDir):
        return (
            path is not None
            and not "__index__" in path.split("/")[-1]
            and not ".venv" in path
            and path.startswith(scriptDir)
            and os.path.isfile(path)
            and path.endswith(".py")
        )


observerInstance = ScriptModificationObserver()
