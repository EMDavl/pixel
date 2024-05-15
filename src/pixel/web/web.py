import asyncio
from uuid import uuid4
import os
import json

from tornado.ioloop import IOLoop

from pixel.commons import Singleton
from pixel.widget_manager import widget_manager
from typing import (
    Optional,
    Union,
    Awaitable,
)
from pixel.web.processors import defaultProcessorManager as procManager

import tornado
from tornado.websocket import WebSocketHandler

from pixel.variables import CommonVariables, VariablesNames


class MessagingManager:

    @classmethod
    def broadcast(cls, message):
        MainWebSocket._broadcast_msg(message)

    @classmethod
    def broadcastWidget(cls, widget):
        MainWebSocket._broadcast_msg(widget.to_message())

    @classmethod
    def sendToUser(cls, sessionId, message):
        MainWebSocket._send_to_user(sessionId, message)

    @classmethod
    def sendWidgetToUser(cls, sessionId, widget):
        MainWebSocket._send_to_user(sessionId, widget.to_message())


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_cookie("sessionId", str(uuid4()))
        self.render("index.html", title=CommonVariables.get_var(VariablesNames.TITLE))


class TornadoIOLoop(metaclass=Singleton):
    def __init__(self, loop: IOLoop):
        self.loop = loop
    
    def addCallback(self, callback):
        self.loop.add_callback(callback)

class MainWebSocket(WebSocketHandler):
    clients = {}

    def open(self, *args, **kwargs):
        session_id = self.request.cookies.get("sessionId")
        if session_id is None:
            raise RuntimeError("Missing session_id")
        MainWebSocket.clients[session_id.value] = self
        iterator = widget_manager.defaultWidgetManager.widgetsIterator()

        for widget, position in iterator:
            try:
                self.write_message({"widget": widget.to_message(), "position": position, "type": "widget"})
            except Exception as e:
                print(e)
                print(widget)
                break

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        if isinstance(message, str):
            print(message)
            parsed = json.loads(message)
            try:
                result = procManager.process(parsed["id"], parsed["args"])
                self.write_message(result)
            except Exception as e:
                self.write_message({"type": "error", "cause": e.__str__()})
    
    def on_close(self) -> None:
        session_id = self.request.cookies.get("sessionId")
        MainWebSocket.clients.pop(session_id.value)

    @classmethod
    def _broadcast_msg(cls, widget):
        for client in MainWebSocket.clients.values():
            client.write_message(widget)

    @classmethod
    def _send_to_user(cls, sessionId, message):
        client = MainWebSocket.clients[sessionId]
        if client is None:
            return False
        client.write_message(message)

async def main():
    settings = {
        "static_path": CommonVariables.get_var(VariablesNames.STATIC_PATH),
        "static_url_prefix": "/static/",
        "template_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/socket", MainWebSocket),
        ],
        **settings,
    )

    app.listen(8888)
    loop = TornadoIOLoop(IOLoop.current())
    TornadoIOLoop.var = loop
    print("Ready to accept connections: http://localhost:8888")
    await asyncio.Event().wait()
