import os
from pixel.api.widgets import Resource, Widget
from typing import Dict, List
from pixel.commons import Singleton, WebSocketMessage, WebSocketMessageType, safe_get
from collections import namedtuple
import pathlib

from pixel.variables import CommonVariables, VariablesNames
from pixel.dataclasses import Movement, WidgetsDiff, WidgetWithNeighbors

WidgetManagerSnapshot = namedtuple("WidgetManagerSnapshot", ["data", "hashes"])


class WidgetManagerDiffChecker:
    def __init__(self, snapshot: WidgetManagerSnapshot) -> None:
        self.hasDiff = False
        self.resourceToBeDeleted = []
        self._snapshot: List[Widget] = snapshot.data
        self._snapshotHashes: Dict[str, Widget] = snapshot.hashes
        self._data: List[Widget] = defaultWidgetManager._data
        self._hashes: Dict[str, Widget] = defaultWidgetManager._hashes
        self.calculateDiff()

    def calculateDiff(self):
        toDelete = self.getToDelete()
        toMove = []
        toCreate = []
        positionsOfOldWidgetsInNewLayout = []

        for actualPosition in range(len(self._data)):
            widget = self._data[actualPosition]

            if widget.hash not in self._snapshotHashes:
                toCreate.append(
                    WidgetWithNeighbors(
                        widget,
                        safe_get(self._data, actualPosition - 1),
                        safe_get(self._data, actualPosition + 1),
                    )
                )
            else:
                positionsOfOldWidgetsInNewLayout.append(widget)

        toMove = self.orderMovements(positionsOfOldWidgetsInNewLayout)
        toCreate = self.orderCreations(toCreate)
        self.diff = WidgetsDiff(toDelete, toCreate, toMove)
        self.hasDiff = (
            len(toDelete) != 0 or len(toCreate) != 0 or self.needPerformMoves(toMove)
        )

    def needPerformMoves(self, moves):
        for i in range(len(self._snapshot)):
            if self._snapshot[i].hash != moves[i].elementHash:
                return True

        return False

    def getToDelete(self):
        toDelete = []
        for entryHash, widget in self._snapshotHashes.items():
            dataEntryWidgets = self._hashes.get(entryHash)
            if dataEntryWidgets is None:
                toDelete.append(entryHash)
                if _isResource(widget):
                    self.resourceToBeDeleted.append(widget.file_name)
        print("Collected elements for deletion")
        return toDelete

    def orderMovements(self, newPositions) -> List[Movement]:
        print("ordering movements")
        orderedMovements = []
        if len(newPositions) == 0:
            return []

        if _isResource(newPositions[0]):
            self.resourceToBeDeleted.append(newPositions[0].file_name)
            newPositions[0].file_name = self._snapshotHashes[
                newPositions[0].hash
            ].file_name

        if len(newPositions) == 1:
            return [Movement(newPositions[0].hash, "", "")]

        orderedMovements.append(
            Movement(newPositions[0].hash, "", newPositions[1].hash)
        )

        for i in range(1, len(newPositions) - 1):
            if _isResource(newPositions[i]):
                self.resourceToBeDeleted.append(newPositions[i].file_name)
                newPositions[i].file_name = self._snapshotHashes[
                    newPositions[i].hash
                ].file_name

            widgetHash = newPositions[i].hash
            after = newPositions[i - 1].hash
            before = newPositions[i + 1].hash
            orderedMovements.append(Movement(widgetHash, after, before))

        if _isResource(newPositions[-1]):
            self.resourceToBeDeleted.append(newPositions[-1].file_name)
            newPositions[-1].file_name = self._snapshotHashes[
                newPositions[-1].hash
            ].file_name

        orderedMovements.append(
            Movement(newPositions[-1].hash, newPositions[-2].hash, "")
        )
        print("ordered movements")
        return orderedMovements

    def orderCreations(self, toCreate):
        print("ordering creations")
        orderedCreations = []
        compareWith = set(self._snapshotHashes)
        processed = 0
        print("toCreate", toCreate)
        print("compareWith", compareWith)

        if len(compareWith) == 0:
            return toCreate

        while len(toCreate) != processed:
            for i in range(len(toCreate)):
                elem = toCreate[i]
                if elem.widget.hash in compareWith:
                    continue
                if (
                    elem.previousElementHash in compareWith
                    or elem.nextElementHash in compareWith
                ):
                    orderedCreations.append(elem)
                    compareWith.add(elem.widget.hash)
                    processed += 1
        print("ordered creations")
        return orderedCreations


class WidgetManager(metaclass=Singleton):
    def __init__(self):
        self._snapshot = []
        self._data: List[Widget] = []
        self._snapshotHashes: Dict[str, Widget] = {}
        self._hashes: Dict[str, Widget] = {}
        self._isScriptRunning = False
        self.cleaner = ResourceCleaner()

    def register(self, hash, obj: Widget):
        obj.hash = self.get_id(hash)
        self._hashes[obj.hash] = obj
        self._data.append(obj)

    def snapshot(self):
        self._snapshot = self._data
        self._snapshotHashes = self._hashes
        self._isScriptRunning = True
        self._data = []
        self._hashes = {}
        return WidgetManagerSnapshot(self._snapshot, self._snapshotHashes)

    def get_id(self, elemHash):
        expectedHash = elemHash
        counter = 0
        while self._hashes.get(expectedHash) is not None:
            expectedHash = elemHash + str(counter)
            counter += 1
        return expectedHash

    def rollback(self):
        self._data = self._snapshot
        self._hashes = self._snapshotHashes
        self._isScriptRunning = False
        self._snapshotHashes = {}
        self._snapshot = []

    def widgetsIterator(self):
        if self._isScriptRunning:
            return self._snapshot.__iter__()

        return self._data.__iter__()

    def executed(self):
        self._isScriptRunning = False

    def cleanup(self, resourceToBeDeleted):
        self.cleaner.cleanup(resourceToBeDeleted)

    def sendDiff(self, diff: WidgetsDiff):
        from pixel.web.web import MainWebSocket

        msg = WebSocketMessage(type=WebSocketMessageType.UPDATE, data=diff.to_message())
        MainWebSocket._broadcast_msg(msg.to_message())


class ResourceCleaner(object):
    def cleanup(self, resourceToBeDeleted):
        for fileName in resourceToBeDeleted:
            self.deleteResource(fileName)

    def deleteResource(self, fileName):
        path = os.path.join(
            CommonVariables.get_var(VariablesNames.STATIC_PATH), fileName
        )
        pathlib.Path(path).unlink(missing_ok=False)


def _isResource(widget):
    return issubclass(widget.__class__, Resource)


defaultWidgetManager = WidgetManager()
