from enum import Enum, auto
from typing import Any, Dict, List


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class WebSocketMessageType(Enum):
    UPDATE = auto()
    WIDGET = auto()
    FORM_RESPONSE = auto()
    ERROR = auto()


class WebSocketMessage():
    def __init__(self, type: WebSocketMessageType, data: Dict[str, Any]) -> None:
        self.type = type
        self.data = data

    def to_message(self):
        return {
            "type": self.type.name,
            "data": self.data
        }

def safe_get(list: List[Any], idx: int):
    if (idx < 0 or idx >= len(list)):
        return None
    else:
        return list[idx]