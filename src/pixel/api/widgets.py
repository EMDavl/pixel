from abc import ABCMeta, abstractmethod
from typing import Any, Dict


class Widget(metaclass=ABCMeta):
    def __init__(self, id):
        self._id = id
    
    @abstractmethod
    def to_message(self) -> Dict[str, Any]:
        ...

class Image(Widget):
    def __init__(self, id, file_name):
        super(Image, self).__init__(id)
        self._file_name = file_name
 
    def to_message(self):
        return {
            "id": self._id,
            "file_name": self._file_name,
            "type": "image"
        }

class Html(Widget):
    def __init__(self, id, file_name):
        super(Html, self).__init__(id)
        self._file_name = file_name
 
    def to_message(self):
        return {
            "id": self._id,
            "file_name": self._file_name,
            "type": "html"
        }

