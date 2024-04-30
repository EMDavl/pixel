import asyncio
from pixel.router.router import Router
import pixel.web.starter as web
import sys

async def main():
    with open(sys.argv[1]) as f:
        file = f.read()
    
    bytecode = compile(file, mode="exec", filename="runner.py")
    exec(bytecode, globals())

    router = Router()
    loop = asyncio.get_event_loop()
    loop.call_later(15, lambda: sendImages(router))
    await web.main()


def sendImages(router):
    print("sending message")
    data = router.data
    for path in data.values():
        web.MainWebSocket.send_message(path)

   