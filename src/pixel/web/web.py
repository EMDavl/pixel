import asyncio
from uuid import uuid4
import os
import json

from pixel.api.widgets import Widget
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

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_cookie("sessionId", str(uuid4()))
        self.render("index.html", title = CommonVariables.get_var(VariablesNames.TITLE))


class MainWebSocket(WebSocketHandler):
    clients = {}

    def open(self, *args, **kwargs):
        session_id = self.request.cookies.get("sessionId")
        if session_id is None:
            raise RuntimeError("Missing session_id")
        MainWebSocket.clients[session_id.value] = self
        data = widget_manager.defaultWidgetManager.data

        for key in data:
            try:
                self.write_message(data[key].to_message())
            except Exception as e:
                print(e)
                print(key, data[key].to_message())

                    
    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        if isinstance(message, str):
            print(message)
            parsed = json.loads(message)
            try:
                result = procManager.process(parsed["id"], parsed["args"])
                self.write_message(result)
            except Exception as e:
                self.write_message({
                    "type": "error",
                    "cause": e.__str__()
                })

    @classmethod
    def broadcast_msg(cls, widget: Widget):
        for client in MainWebSocket.clients.values():
            client.write_message(widget.to_message)

async def main():
    settings = {
        "static_path": CommonVariables.get_var(VariablesNames.STATIC_PATH),
        "static_url_prefix": "/static/",
        "template_path": os.path.join(os.path.dirname(__file__), "static")
    }
    
    app = tornado.web.Application(
        [
            (r"/", MainHandler), 
            (r"/socket", MainWebSocket),
        ], **settings)
    
    app.listen(8888)
    
    print("Ready to accept connections: http://localhost:8888")
    await asyncio.Event().wait()
