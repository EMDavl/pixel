from pixel.api.widgets import Widget
from typing import Dict
from pixel.commons import Singleton

class WidgetManager(metaclass=Singleton):
    def __init__(self):
        self.data: Dict[int, Widget] = {}

    def register(self, id, obj: Widget):
        self.data[id] = obj
    
    @classmethod
    def create(cls):
        WidgetManager()

defaultWidgetManager = WidgetManager()