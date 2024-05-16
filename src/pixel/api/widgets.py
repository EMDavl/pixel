from abc import ABCMeta
from enum import Enum, auto
from typing import Any, Dict
from hashlib import md5
import uuid

class WidgetType(Enum):
    ## COMMON WIDGETS
    IMAGE = auto()
    HTML = auto()
    MARKDOWN = auto()

    ## LAYOUT
    ROW = auto()
    COLUMN = auto()

    ## FORM RELATED
    FORM = auto()

    ### INPUTS
    NUMBER_INPUT = auto()

    ### OUTPUTS
    IMAGE_OUTPUT = auto()
    TEXT_OUTPUT = auto()


class Widget(metaclass=ABCMeta):
    def __init__(self, widgetHash, widgetType: WidgetType):
        self._type = widgetType
        self.hash = widgetHash
        self.id = str(uuid.uuid4())

    def to_message(self) -> Dict[str, Any]:
        return {"id": self.id, "hash": self.hash, "type": self._type.name.lower()}


class Container(Widget):
    pass

class Resource(Widget):
    def __init__(self, widgetHash, widgetType: WidgetType, file_name):
        super().__init__(widgetHash, widgetType)
        self.file_name = file_name
    
    def to_message(self):
        message = super().to_message()
        message["file_name"] = self.file_name
        return message


class ImageFile(Resource):
    def __init__(self, widgetHash, file_name):
        super().__init__(widgetHash, WidgetType.IMAGE, file_name)

class Html(Resource):
    def __init__(self, hash, file_name):
        super(Html, self).__init__(hash, WidgetType.HTML, file_name)

class Markdown(Widget):
    def __init__(self, hash, markdown):
        super(Markdown, self).__init__(hash, WidgetType.MARKDOWN)
        self._markdown = markdown

    def to_message(self) -> Dict[str, Any]:
        message = super().to_message()
        message["markdown"] = self._markdown
        return message


class Row(Container):
    def __init__(self, widgets):
        super(Row, self).__init__(_getHashForContainer(widgets), WidgetType.ROW)
        self._widgets = widgets

    def to_message(self) -> Dict[str, Any]:
        message = super().to_message()
        message["widgets"] = [
            widgetMessage.to_message() for widgetMessage in self._widgets
        ]
        return message


class Column(Container):
    def __init__(self, widgets):
        super(Column, self).__init__(_getHashForContainer(widgets), WidgetType.COLUMN)
        self._widgets = widgets

    def to_message(self) -> Dict[str, Any]:
        message = super().to_message()
        message["widgets"] = [
            widgetMessage.to_message() for widgetMessage in self._widgets
        ]
        return message


## FORM RELATED
class Form(Widget):
    def __init__(self, inputWidgets, output):
        super(Form, self).__init__(_getHashForContainer(inputWidgets), WidgetType.FORM)
        self._input = inputWidgets
        self._output = output

    def to_message(self) -> Dict[str, Any]:
        message = super().to_message()
        message["input"] = [inputElem.to_message() for inputElem in self._input]
        message["output"] = self._output.to_message()
        return message


### INPUTS
class Input(Widget, metaclass=ABCMeta):
    def __init__(self, label, widgetType):
        super(Input, self).__init__(md5((label + widgetType.name).encode()).hexdigest(), widgetType)
        self._label = label


class Number(Input):
    def __init__(self, label):
        super(Number, self).__init__(label, WidgetType.NUMBER_INPUT)

    def to_message(self) -> Dict[str, Any]:
        message = super().to_message()
        message["label"] = self._label
        return message


### OUTPUTS
class Output(Widget, metaclass=ABCMeta):
    def __init__(self, label, widgetType):
        super(Output, self).__init__(md5((label + widgetType.name).encode()).hexdigest(), widgetType)
        self._label = label

    def to_message(self) -> Dict[str, Any]:
        msg = super().to_message()
        msg["label"] = self._label
        return msg


class ImageOut(Output):
    def __init__(self, label):
        super(ImageOut, self).__init__(label, WidgetType.IMAGE_OUTPUT)


class TextOutput(Output):
    def __init__(self, label):
        super().__init__(label, WidgetType.TEXT_OUTPUT)


def _getHashForContainer(widgets):
    hashString = ""
    hashes = []
    for widget in widgets:
        hashes.append(widget.hash)
    for hash in hashes:
        hashString += hash
    return md5(hashString.encode()).hexdigest()