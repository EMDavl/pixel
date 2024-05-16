import os
from re import I
from pixel.api.widgets import Resource, Widget
from typing import List
from pixel.commons import Singleton, resetId
from collections import namedtuple
import pathlib

from pixel.variables import CommonVariables, VariablesNames

WidgetManagerSnapshot = namedtuple("WidgetManagerSnapshot", ["data", "hashes"])
PositionedWidget = namedtuple("PositionedWidget", ["widget", "position"])
WidgetWithNeighbors = namedtuple("WidgetWithNeighbors", ["widget", "after", "before"])
Movement = namedtuple("Movement", ["elementHash", "after", "before"])
WidgetsDiff = namedtuple("WidgetsDiff", ["toDelete", "toCreate", "toMove"])


class DiffChecker:
    def __init__(self, snapshot: WidgetManagerSnapshot) -> None:
        self.hasDiff = False
        self._snapshot = snapshot.data
        self._snapshotHashes = snapshot.hashes
        self._data = defaultWidgetManager._data
        self._hashes = defaultWidgetManager._hashes

        self.calculateDiff()

    def calculateDiff(self):
        toDelete = []
        toMove = []
        toCreate = []
        positionsOfOldWidgetsInNewLayout = []

        for widget, _ in self._snapshot:
            if widget.hash not in self._hashes:
                toDelete.append(widget.hash)

        for actualPosition in range(len(self._data)):
            widget, _ = self._data[actualPosition]

            if widget.hash not in self._snapshotHashes:
                toCreate.append(
                    WidgetWithNeighbors(
                        widget,
                        (
                            self._data[actualPosition - 1].widget.hash
                            if self._data[actualPosition - 1] is not None
                            else None
                        ),
                        (
                            self._data[actualPosition + 1].widget.hash
                            if self._data[actualPosition + 1] is not None
                            else None
                        ),
                    )
                )
            else:
                positionsOfOldWidgetsInNewLayout.append(
                    PositionedWidget(widget, actualPosition)
                )
        toMove = self.orderMovements(positionsOfOldWidgetsInNewLayout)
        toCreate = self.orderCreations(toCreate)
        self.diff = WidgetsDiff(toDelete, toCreate, toMove)
        self.hasDiff = len(toDelete) != 0 or len(toCreate) != 0 or len(toMove) != 0

    def getOldPosition(self, widgetHash):
        for i in range(len(self._snapshot)):
            if self._snapshot[i].widget.hash == widgetHash:
                return i

    def orderMovements(self, newPositions) -> List[Movement]:
        orderedMovements = []
        if len(newPositions) == 0:
            return []
        if len(newPositions) == 1:
            return [Movement(newPositions[0].widget.hash, "", "")]

        orderedMovements.append(
            Movement(newPositions[0].widget.hash, "", newPositions[1].widget.hash)
        )
        for i in range(1, len(newPositions) - 1):
            widgetHash = newPositions[i].widget.hash
            after = newPositions[i - 1].widget.hash
            before = newPositions[i + 1].widget.hash
            orderedMovements.append(Movement(widgetHash, after, before))

        orderedMovements.append(
            Movement(newPositions[-1].widget.hash, newPositions[-2].widget.hash, "")
        )
        return orderedMovements

    def orderCreations(self, toCreate):
        orderedCreations = []
        compareWith = set(self._snapshotHashes)
        processed = 0
        while len(toCreate) != processed:
            for i in range(len(toCreate)):
                elem = toCreate[i]
                if elem.widget.hash in compareWith:
                    continue
                if elem.after in compareWith or elem.before in compareWith:
                    orderedCreations.append(elem)
                    compareWith.add(elem.widget.hash)
                    processed += 1
        return orderedCreations


class WidgetManager(metaclass=Singleton):
    def __init__(self):
        self._snapshot = []
        self._data: List[PositionedWidget] = []
        self._snapshotHashes = {}
        self._hashes = {}
        self._isScriptRunning = False

    def register(self, hash, obj: Widget):
        if obj.hash is None:
            obj.hash = hash
        self._hashes[obj.hash] = obj
        self._data.append(PositionedWidget(obj, len(self._data)))

    def snapshot(self):
        self._snapshot = self._data
        self._snapshotHashes = self._hashes
        self._isScriptRunning = True
        self._data = []
        self._hashes = {}
        resetId()
        return WidgetManagerSnapshot(self._snapshot, self._snapshotHashes)

    def widgetsIterator(self):
        if self._isScriptRunning:
            return self._snapshot.__iter__()

        return self._data.__iter__()

    def executed(self):
        self._isScriptRunning = False

    def cleanup(self):
        if True:
            return
        for widget in self._snapshot:
            if self.resourceHasToBeDeleted(widget.widget):
                self.deleteResource(widget.widget)

    def resourceHasToBeDeleted(self, widget):
        return issubclass(widget.__class__, Resource)

    def deleteResource(self, widget):
        path = os.path.join(
            CommonVariables.get_var(VariablesNames.STATIC_PATH), widget.file_name
        )
        pathlib.Path(path).unlink(missing_ok=False)

    def sendDiff(self, diff: WidgetsDiff):
        from pixel.web.web import MessagingManager

        MessagingManager.broadcast(
            message={
                "type": "update",
                "toDelete": diff.toDelete,
                "toMove": diff.toMove,
                "toCreate": [
                    [widget[0].to_message(), widget[1], widget[2]]
                    for widget in diff.toCreate
                ],
            }
        )

    @classmethod
    def create(cls):
        WidgetManager()


defaultWidgetManager = WidgetManager()
