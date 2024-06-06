import traceback
from uuid import uuid4
import os
import jsonpickle
from concurrent.futures import ThreadPoolExecutor
from pixel.authorization.auth import AuthorizationManager
from pydantic import ValidationError
from tornado.ioloop import IOLoop
from tornado import gen
import json

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


class AuthHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_signed_cookie("user")


class LoginHandler(AuthHandler):
    def get(self):
        # if self.get_current_user:
            # self.redirect("/")
            # return
        self.render("login.html", title="Login")

    def post(self):
        login = self.get_argument("login")
        password = self.get_argument("password")

        if (
            login is not None
            and password is not None
            and len(password) >= 8
            and AuthorizationManager.valid_credentials(login, password)
        ):
            self.set_signed_cookie("user", login)
            self.redirect("/")
            return
        
        self.redirect("/login?success=false")


class MainHandler(AuthHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
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


class MainWebSocket(WebSocketHandler, ):
    clients = {}

    def get_current_user(self):
        return self.get_signed_cookie("user")

    def open(self, *args, **kwargs):
        user = self.get_current_user()
        if not user:
            self.redirect("/login")
            return

        MainWebSocket.clients[user] = self
        self.send_widgets()

    def send_widgets(self):
        iterator = widget_manager.defaultWidgetManager.widgetsIterator()

        for widget in iterator:
            msg = WebSocketMessage(WebSocketMessageType.WIDGET, widget.to_message())
            try:
                self.write_message(msg.to_message())
            except Exception as e:
                print(msg.to_message())
                traceback.print_exc()
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
                traceback.print_exc()
                self.write_message(
                    WebSocketMessage(
                        WebSocketMessageType.ERROR, {"cause": str(e)}
                    ).to_message()
                )

    def on_close(self) -> None:
        MainWebSocket.clients.pop(self.get_current_user())

    @classmethod
    def _broadcast_msg(cls, message):
        for client in MainWebSocket.clients.values():
            client.write_message(message)


async def main():
    settings = {
        "static_path": CommonVariables.get_var(VariablesNames.STATIC_PATH),
        "static_url_prefix": "/static/",
        "template_path": os.path.join(os.path.dirname(__file__), "static"),
        'cookie_secret': "PUPI SECRET"
    }
    paths = [
            (r"/api/.*", ApiHandler),
            (r"/", MainHandler),
            (r"/socket", MainWebSocket),
        ]

    if (CommonVariables.get_var(VariablesNames.AUTH_ENABLED)):
        paths.append((r"/login", LoginHandler))

    app = tornado.web.Application(
        paths,
        **settings,
    )

    app.listen(8888)
    loop = TornadoIOLoop(IOLoop.current())
    TornadoIOLoop.var = loop
    print("Ready to accept connections: http://localhost:8888")
    return app


class TornadoIOLoop(metaclass=Singleton):
    def __init__(self, loop: IOLoop):
        self.loop = loop

    def addCallback(self, callback):
        self.loop.add_callback(callback)
