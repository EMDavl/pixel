from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import os
import sys
from pixel.variables import CommonVariables, VariablesNames
from pixel.commons import Singleton
from typing import List, Set


class ScriptModificationHandler(FileSystemEventHandler):
    def __init__(self, path_to_script, dependencies) -> None:
        super().__init__()
        self._scriptPath = path_to_script
        self._dependencies = dependencies

    def on_modified(self, event: FileSystemEvent) -> None:
        # To prevent circular dependencies
        from pixel.cli.executor import ScriptEvent

        if event.is_directory:
            return
        path = os.path.abspath(event.src_path)
        if path == self._scriptPath or path in self._dependencies:
            CommonVariables.get_var(VariablesNames.EVENT_QUEUE).put(ScriptEvent.RERUN)


class ScriptObserverBase:
    def reloadObserver(self): ...

    def getDependencies(self, scriptDir) -> Set[str]: ...

    def isValidFile(self, path, scriptDir) -> bool: ...


class ScriptModificationObserver(ScriptObserverBase, metaclass=Singleton):

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
        dependencies = self.get_dependencies(scriptDir)
        
        eventHandler = ScriptModificationHandler(scriptPath, dependencies)

        self._watches.add(self.obs.schedule(eventHandler, scriptDir, True))

    def get_dependencies(self, scriptDir):
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

                paths = [
                    os.path.abspath(str(p))
                    for p in potential_paths
                    if self.is_valid_file(p, scriptDir)
                ]
                if paths:
                    all_paths.update(paths)
        return all_paths

    def is_valid_file(self, path, scriptDir):
        return (
            path is not None
            and not "__index__" in path.split("/")[-1]
            and not ".venv" in path
            and path.startswith(scriptDir)
            and os.path.isfile(path)
            and path.endswith(".py")
        )


class NoOpObserver(ScriptObserverBase):
    def getDependencies(self, scriptDir):
        pass

    def isValidFile(self, path, pathDir):
        pass

    def reloadObserver(self):
        pass


observer_instance = (
    ScriptModificationObserver()
)  # if (len(sys.argv) >= 3 and sys.argv[3] == 'd') else NoOpObserver()
