import asyncio
from uuid import uuid4
import os
from pixel.router import router
from typing import (
    Optional,
    Union,
    Awaitable,
)

import tornado
from tornado.websocket import WebSocketHandler

from pixel.variables import CommonVariables, VariablesNames

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_cookie("sessionId", str(uuid4()))
        self.render("index.html")


class MainWebSocket(WebSocketHandler):
    clients = {}

    def open(self, *args, **kwargs):
        session_id = self.request.cookies.get("sessionId")
        if session_id is None:
            raise RuntimeError("Missing session_id")
        MainWebSocket.clients[session_id.value] = self
        data = router.Router().data
        print("Sending messages for new client", data)
        for key in data:
            self.write_message({
                "elementId": key,
                "imageUrl": data[key],
            })
        

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        if isinstance(message, str):
            print(message)

    @classmethod
    def broadcast_img(cls, img_path, elementId):
        for client in MainWebSocket.clients.values():
            client.write_message({
                "elementId": elementId,
                "imageUrl": img_path,
            })

async def main():
    settings = {
        "static_path": CommonVariables.get_var(VariablesNames.STATIC_PATH),
        "static_url_prefix": "/static/",
        "template_path": os.path.join(os.path.dirname(__file__), "static")
    }
    
    app = tornado.web.Application(
        [
            (r"/", MainHandler), 
            (r"/socket", MainWebSocket)
        ], **settings)
    
    app.listen(8888)
    
    print("Ready to accept connections: http://localhost:8888")
    await asyncio.Event().wait()
