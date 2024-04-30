import asyncio
import os
import sys
from typing import (
    Optional,
    Union,
    Awaitable,
)

import tornado
from tornado.websocket import WebSocketHandler

class MainHandler(tornado.web.RequestHandler):
    app: tornado.web.Application

    def get(self):
        self.set_cookie("sessionId", "someid")
        self.render("static/index.html")


class MainWebSocket(WebSocketHandler):
    clients = {}    
    def open(self, *args, **kwargs):
        print(1)
        session_id = self.request.cookies.get("sessionId")
        if session_id is None:
            raise RuntimeError("Missing session_id")
        MainWebSocket.clients[session_id.value] = self

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        if isinstance(message, str):
            print(message)

    @classmethod
    def send_message(cls, img_path):
        for client in MainWebSocket.clients.values():
            client.write_message({
                "imageUrl": img_path,
            })

async def main():
    settings = {
        "static_path": os.path.join(os.path.dirname(sys.argv[1]), "static"),
        "static_url_prefix": "/static/",
    }
    app = tornado.web.Application(
        [(r"/", MainHandler), (r"/socket", MainWebSocket)]
        ,**settings)
    settings = app.settings
    MainHandler.app = app
    for key in settings.keys():
        print(settings[key])
    app.listen(8888)
    await asyncio.Event().wait()
