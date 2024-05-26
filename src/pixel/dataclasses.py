from abc import ABCMeta

from pixel.api.widgets import WidgetType


class FormOutput(metaclass=ABCMeta):
    def __init__(self, outputType, formId) -> None:
        self.outputType = outputType
        self.formId = formId


    def to_message(self):
        return {
            "outputType": self.outputType.name,
            "formId": self.formId
        }

class ImageFormOutput(FormOutput):
    def __init__(self, formId, bytes) -> None:
        super().__init__(WidgetType.IMAGE_OUTPUT, formId)
        self.bytes = bytes
    
    def to_message(self):
        msg = super().to_message()
        msg["bytes"] = self.bytes
        return msg


class TextFormOutput(FormOutput):
    def __init__(self, formId, text) -> None:
        super().__init__(WidgetType.TEXT_OUTPUT, formId)
        self.text = text
    
    def to_message(self):
        msg = super().to_message()
        msg["text"] = self.text
        return msg


class Movement(object):
    def __init__(self, elementHash, previousElementHash, nextElementHash) -> None:
        self.elementHash = elementHash
        self.previousElementHash = previousElementHash
        self.nextElementHash = nextElementHash

    def to_message(self):
        return {
            "elementHash": self.elementHash,
            "previousElementHash": self.previousElementHash,
            "nextElementHash": self.nextElementHash,
        }

class WidgetsDiff(object):
    def __init__(self, toDelete, toCreate, toMove) -> None:
        self.toDelete = toDelete
        self.toCreate = toCreate
        self.toMove = toMove

    def to_message(self):
        return {
                "toDelete": self.toDelete,
                "toMove": [elem.to_message() for elem in self.toMove],
                "toCreate": [
                    widget.to_message() for widget in self.toCreate
                ],
        }
    

class WidgetWithNeighbors(object):
    def __init__(self, widget, previousElement, nextElement) -> None:
        self.widget = widget
        self.previousElementHash = previousElement.hash if previousElement is not None else None
        self.nextElementHash = nextElement.hash if nextElement is not None else None

   
    def to_message(self):
        return {
            "widget": self.widget.to_message(),
            "previousElementHash": self.previousElementHash,
            "nextElementHash": self.nextElementHash,
        }

