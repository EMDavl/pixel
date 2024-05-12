from abc import ABCMeta, abstractmethod
from typing import Any, Dict


class Widget(metaclass=ABCMeta):
    def __init__(self, id):
        self._id = id

    @abstractmethod
    def to_message(self) -> Dict[str, Any]: ...


class ImageFile(Widget):
    def __init__(self, id, file_name):
        super(ImageFile, self).__init__(id)
        self._file_name = file_name

    def to_message(self):
        return {"id": self._id, "file_name": self._file_name, "type": "image"}


class Html(Widget):
    def __init__(self, id, file_name):
        super(Html, self).__init__(id)
        self._file_name = file_name

    def to_message(self):
        return {"id": self._id, "file_name": self._file_name, "type": "html"}


class Markdown(Widget):
    def __init__(self, id, markdown):
        super(Markdown, self).__init__(id)
        self._markdown = markdown

    def to_message(self) -> Dict[str, Any]:
        return {"id": self._id, "markdown": self._markdown, "type": "markdown"}


class Row(Widget):
    def __init__(self, id, widgets):
        super(Row, self).__init__(id)
        self._widgets = widgets

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": "row",
            "widgets": [widgetMessage.to_message() for widgetMessage in self._widgets],
        }


class Column(Widget):
    def __init__(self, id, widgets):
        super(Column, self).__init__(id)
        self._widgets = widgets

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": "column",
            "widgets": [widgetMessage.to_message() for widgetMessage in self._widgets],
        }


class Input(Widget, metaclass=ABCMeta):
    def __init__(self, id, label):
        super(Input, self).__init__(id)
        self._label = label


class Number(Input):
    def __init__(self, label):
        super(Number, self).__init__(None, label)

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "label": self._label,
            "type": "number_input",
        }


class Output(Widget, metaclass=ABCMeta):
    def __init__(self, id, label, outputType):
        super(Output, self).__init__(id)
        self._label = label
        self.outputType = outputType


class ImageOut(Output):
    def __init__(self, label):
        super(ImageOut, self).__init__(None, label, "image_output")

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "label": self._label,
            "type": "image_output",
        }

class TextOutput(Output):
    def __init__(self, label):
        super().__init__(None, label, "text_output")

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "label": self._label,
            "type": self.outputType
        }

class Form(Widget):
    def __init__(self, id, inputWidgets, output):
        super(Form, self).__init__(id)
        self._input = inputWidgets
        self._output = output

    def to_message(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "type": "form",
            "input": [inputElem.to_message() for inputElem in self._input],
            "output": self._output.to_message(),
        }
