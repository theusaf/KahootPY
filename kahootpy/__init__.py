import time
import asyncio
import importlib
import ssl
from pymitter import EventEmitter
from aiocometd import Client
from numbers import Number
from .src.util.token import resolve

class KahootClient(EventEmitter):
    def __init__(self):
        super().__init__()
        self.gameid = None
        self.loggingMode = False
        self.modules = {}
        self.handlers = {}
        self.data = {}
        self.classes = {}
        self.socket = None
        for module in ("answer","backup","extraData","feedback","gameReset","main","nameAccept","podium","questionEnd","questionReady","questionStart","quizEnd","quizStart","teamAccept","teamTalk","timeOver"):
            f = getattr(importlib.import_module(f".src.modules.{module}","KahootPY"),"main")
            f(self)
    async def join(self,pin,name=None,team=["Player 1","Player 2","Player 3","Player 4"]):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        async def go():
            self.gameid = pin
            data = await resolve(self.gameid,self)
            token = data["token"]
            client = Client(f"wss://kahoot.it/cometd/{self.gameid}/{token}")
            self.socket = client
            await client.open()
            await client.subscribe("/service/controller")
            await client.subscribe("/service/status")
            await client.subscribe("/service/player")
            await self._send(self.classes["LiveClientHandshake"](0))
            async for message in client:
                # Handle messages
                self._message(message)
            await client.close()
        loop.create_task(go())
        return await future
    def _message(self,message):
        if not self.loggingMode:
            d = json.dumps(message)
            print(f"RECV: {d}")
        for i in self.handlers:
            self.handlers[i](message)
    async def _send(self,message,callback=None):
        if not self.loggingMode:
            d = json.dumps(message)
            print(f"SEND: {d}")
        if self.socket and not self.socket.closed:
            success = True
            try:
                c = message["channel"]
                m = message.get("data")
                await self.socket.publish(c,m)
            except Exception as e:
                success = False
            if success:
                callback(True)
            else:
                callback(False)
