from enum import Enum
from enum import auto

class VariablesNames(Enum):
    STATIC_PATH = auto()
    SCRIPT_NAME = auto()


class CommonVariables():
    data = {}

    @classmethod
    def get_var(cls, name: VariablesNames):
        return CommonVariables.data[name]

    @classmethod
    def set_var(cls, name: VariablesNames, value):
        CommonVariables.data[name] = value