import asyncio
from uuid import uuid4
import os
import jsonpickle
from concurrent.futures import ThreadPoolExecutor
from pydantic import ValidationError
from tornado.ioloop import IOLoop
from tornado import gen

from pixel.commons import Singleton, WebSocketMessage, WebSocketMessageType
from pixel.widget_manager import widget_manager
from typing import (
    Optional,
    Union,
    Awaitable,
)
from pixel.web.processors import defaultProcessorManager as procManager
from pixel.web.exceptions import NotExists

import tornado
from tornado.websocket import WebSocketHandler

from pixel.variables import CommonVariables, VariablesNames

executor = ThreadPoolExecutor(8)


class MessagingManager:

    @classmethod
    def broadcast(cls, message: WebSocketMessage):
        MainWebSocket._broadcast_msg(message.to_message())


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_cookie("sessionId", str(uuid4()))
        self.render("index.html", title=CommonVariables.get_var(VariablesNames.TITLE))


class ApiHandler(tornado.web.RequestHandler):

    def set_default_headers(self) -> None:
        self.set_header("Content-Type", "application/json")

    @gen.coroutine
    def post(self):
        try:
            if self.request.uri is not None:
                body = self.request.body
                uri = self.request.uri[4:]
                response = yield executor.submit(
                    lambda: procManager.processApi(uri, body)
                )
                self.write(jsonpickle.encode(response, unpicklable=False))
        except NotExists:
            self.set_status(404, "Requested uri doesn't exist")
            response = {"reason": "Path not found"}
            self.write(response)
        except TypeError as e:
            self.set_status(400, "Failed to map request body")
            self.write({"reason": str(e)})
        except ValidationError as e:
            errors = [err["msg"] for err in e.errors()]
            self.set_status(400, "Failed to map request body")
            self.write({"reason": errors})


class MainWebSocket(WebSocketHandler):
    clients = {}

    def open(self, *args, **kwargs):
        session_id = self.request.cookies.get("sessionId")
        if session_id is None:
            self.write_message(
                WebSocketMessage(
                    WebSocketMessageType.ERROR, {"cause": "Missing session id"}
                ).to_message()
            )
            return
        MainWebSocket.clients[session_id.value] = self
        self.send_widgets()
    
    def send_widgets(self):
        iterator = widget_manager.defaultWidgetManager.widgetsIterator()

        for widget in iterator:
            try:
                msg = WebSocketMessage(WebSocketMessageType.WIDGET, widget.to_message())
                self.write_message(msg.to_message())
            except Exception as e:
                print(e)
                self.write_message(
                    WebSocketMessage(
                        WebSocketMessageType.ERROR, {"cause": str(e)}
                    ).to_message()
                )

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        if isinstance(message, str):
            parsed = json.loads(message)
            try:
                result = procManager.processForm(parsed["id"], parsed["args"])
                self.write_message(result.to_message())
            except Exception as e:
                self.write_message(
                    WebSocketMessage(
                        WebSocketMessageType.ERROR, {"cause": str(e)}
                    ).to_message()
                )

    def on_close(self) -> None:
        session_id = self.request.cookies.get("sessionId")
        MainWebSocket.clients.pop(session_id.value)

    @classmethod
    def _broadcast_msg(cls, widget):
        for client in MainWebSocket.clients.values():
            client.write_message(widget)


async def main():
    settings = {
        "static_path": CommonVariables.get_var(VariablesNames.STATIC_PATH),
        "static_url_prefix": "/static/",
        "template_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    app = tornado.web.Application(
        [
            (r"/api/.*", ApiHandler),
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


class TornadoIOLoop(metaclass=Singleton):
    def __init__(self, loop: IOLoop):
        self.loop = loop

    def addCallback(self, callback):
        self.loop.add_callback(callback)
