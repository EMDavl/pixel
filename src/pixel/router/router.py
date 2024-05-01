from pixel.api.widgets import Widget
from typing import Dict


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Router(metaclass=Singleton):
    def __init__(self):
        self.data: Dict[int, Widget] = {}

    def add(self, id, obj: Widget):
        self.data[id] = obj
    
    @classmethod
    def create(cls):
        Router()