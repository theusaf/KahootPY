from pymitter import EventEmitter
from .src.util.copyfunc import copy_func
from .src.util.ChallengeHandler import ChallengeHandler
import threading
import time
import sys
import copy
import types
import functools
import importlib
import asyncio
import json as JSON
from websocket import WebSocketApp as ws
from numbers import Number
from .src.util.errors import *
from .src.util.token import *
from user_agent import generate_user_agent as UserAgent

loop = asyncio.get_event_loop()

class client(EventEmitter):
    def __init__(self,options={}):
        super().__init__()
        self.defaults = {}
        # Assign the default values
        for i in client._defaults:
            if callable(client._defaults[i]):
                # TODO: Check if this is needed.
                self.defaults[i] = copy_func(client._defaults[i])
                continue
            self.defaults[i] = copy.deepcopy(client._defaults[i])
        # Assign values from options
        self.defaults["options"].update(options.get("options") or {})
        self.defaults["modules"].update(options.get("modules") or {})
        self.defaults["proxy"] = options.get("proxy") or self.defaults["proxy"]
        self.defaults["wsproxy"] = options.get("wsproxy") or self.defaults["wsproxy"]
        # Set up some data
        self.classes = {}
        self.handlers = {}
        self.waiting = {}
        self.data = {}
        self.cid = None
        self.gameid = None
        self.socket = None
        self.settings = None
        self.questionStartTime = None
        self.reconnectRecovery = None
        self.feedbackTime = None
        self.connected = False
        self.name = None
        self.quiz = None
        self.clientId = None
        self.loggingMode = False
        self.lastEvent = (None,None)
        self._timesync = {}
        self.twoFactorResetTime = None
        self.disconnectReason = None
        # Import modules
        for mod in self.defaults["modules"]:
            if self.defaults["modules"].get(mod) or self.defaults["modules"].get(mod) == None:
                try:
                    f = getattr(importlib.import_module(".src.modules." + mod,"kahoot"),"main")
                    f(self)
                except Exception:
                    pass
        m = getattr(importlib.import_module(".src.modules.main","kahoot"),"main")
        m(self)

        self.userAgent = UserAgent()
        self.messageId = 0

    @classmethod
    def defaults(cls,options={}):
        c = copy.deepcopy(cls)
        c._defaults.update(options)
        return c

    @classmethod
    def join(cls,*args):
        c = cls()
        e = c.join(args)
        return {
            "event": e,
            "client": c
        }

    async def answerTwoFactorAuth(self,steps=[0,1,2,3]):
        if self.gameid[0] == "0":
            raise "Cannot answer two steps in Challenges"
        wait = int(time.time() * 1000) - self.twoFactorResetTime
        if wait < 250:
            await asyncio.sleep((250 - wait) / 1000)
        promise = loop.create_future()
        def waiter(r):
            if not r or not r["successful"]:
                promise.set_exception(SendFailException(r))
            else:
                promise.set_result(r)
        await self._send(self.classes["LiveTwoStepAnswer"](self,steps),waiter)
        return promise

    async def join(self,pin,name=None,team=["Player 1","Player 2","Player 3","Player 4"]):
        self.gameid = str(pin)
        self.name = name
        settings = await self._createHandshake()
        self.settings = settings
        await asyncio.sleep(1)
        await self._send(self.classes["LiveJoinPacket"](self,name))
        promise = loop.create_future()
        async def JoinFinish(message):
            if message["channel"] == "/service/status":
                self.emit("status",message["data"])
                if message["data"]["status"] == "LOCKED":
                    promise.set_exception(GameLockedError(message["data"]))
                    return
                del self.handlers["JoinFinish"]
                self.disconnectReason = message.get("description")
                self.leave(True)
            elif message["channel"] == "/service/controller" and message.get("data") and message["data"].get("type") == "loginResponse":
                if message["data"].get("error"):
                    promise.set_exception(JoinFailError(message.get("error")))
                    if str(message["data"].get("description")).lower() != "duplicate name":
                        self.disconnectReason = message.get("description")
                        self.leave(True)
                else:
                    self.cid = message["data"]["cid"]
                    if settings.get("gameMode") == "team":
                        await asyncio.sleep(1)
                        if team != False:
                            try:
                                await self.joinTeam(team,True)
                            except Exception:
                                pass
                            self.emit("Joined",settings)
                            if not self.settings["twoFactorAuth"]:
                                self.connected = True
                            else:
                                self.emit("TwoFactorReset")
                            promise.set_result(settings)
                        else:
                            self.emit("Joined",settings)
                            if self.settings["twoFactorAuth"]:
                                self.emit("TwoFactorReset")
                            promise.set_result(settings)
                    else:
                        self.emit("Joined",settings)
                        if not self.settings["twoFactorAuth"]:
                            self.connected = True
                        else:
                            self.emit("TwoFactorReset")
                        promise.set_result(settings)
                del self.handlers["JoinFinish"]
        self.handlers["JoinFinish"] = JoinFinish
        return promise

    async def joinTeam(self,team=["Player 1","Player 2","Player 3","Player 4"],s=False):
        if self.gameid[0] == "0" or self.settings.get("gameMode") != "team" or not self.socket or self.socket["readyState"] != 1:
            raise TeamJoinError("Invalid gamemode")
        promise = loop.create_future()
        def waiter(r):
            if not r or not r["successful"]:
                promise.set_exception(SendFailException(r))
            else:
                not s and self.emit("Joined",self.settings)
                if not self.settings["twoFactorAuth"]:
                    self.connected = True
                else:
                    not s and self.emit("TwoFactorReset")
                promise.set_result(r)
        self._send(self.classes["LiveJoinTeamPacket"](self,team),waiter)
        return promise

    async def leave(self,safe=False):
        self._send(self.classes["LiveLeavePacket"](self))
        if not safe:
            self.disconnectReason = "Client Left"
        await asyncio.sleep(0.5)
        if not self.socket:
            return
        self.socket.close()

    async def _createHandshake(self):
        if self.socket and self.socket["readyState"] == 1 and self.settings:
            return self.settings
        data = await resolve(self.gameid,self)
        promise = loop.create_future()
        if data.get("data") and not data["data"].get("isChallenge"):
            # Either a url or a websocket object
            token = data["token"]
            options = client._defaults["wsproxy"](f"wss://kahoot.it/cometd/{self.gameid}/{token}")
            if type(options) is not str and isinstance(options.get("readyState"),Number) and callable(options.get("close")):
                self.socket = options
            else:
                self.socket = ws(options)
        else:
            self.socket = ChallengeHandler(self,data)
        def onclose():
            self.emit("Disconnect",self.disconnectReason or "Lost Connection")
            self.socket.close = None
        def onopen():
            self._send(self.classes["LiveClientHandshake"](0))
        def onmessage(message):
            self._message(message)
            pass
        def onerror():
            self.emit("HandshakeFailed")
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket.close = None
        def HandshakeComplete():
            promise.set_result(data.get("data"))
        def HandshakeFailed():
            promise.set_exception(JoinFailError(None))
        self.socket.on_open = onopen
        self.socket.on_close = onclose
        self.socket.on_message = onmessage
        self.socket.on_error = onerror
        self.on("HandshakeComplete",HandshakeComplete)
        self.on("HandshakeFailed",HandshakeFailed)
        return promise

    async def _send(self,message,callback=None):
        if self.loggingMode:
            print("SEND: " + JSON.dumps(message))
        if self.socket and callable(self.socket.close):
            if message == None:
                raise "empty_message"
            promise = loop.create_future()
            if isinstance(message,list):
                self.messageId = self.messageId + 1
                message[0]["id"] = str(self.messageId)
                await self.socket.send(JSON.dumps(message))
                promise.set_result(None)
            else:
                self.messageId = self.messageId + 1
                message["id"] = str(self.messageId)
                await self.socket.send(JSON.dumps([message]))
                promise.set_result(None)
            if callback:
                id = str(self.messageId)
                self.waiting[id] = callback
                await asyncio.sleep(10)
                if self.waiting.get(id):
                    callback(None)
                    del self.waiting[id]

    def _message(self,message):
        if self.loggingMode:
            print("RECV: " + message)
        for i in self.handlers:
            self.handlers[i](JSON.loads(message)[0])

    def _emit(self,evt,payload=None):
        if not self.quiz:
            self.quiz = {}
        if payload and payload.get("quizQuestionAnswers"):
            self.quiz["quizQuestionAnswers"] = payload["quizQuestionAnswers"]
        if payload and payload.get("questionIndex"):
            if not self.quiz.get("currentQuestion"):
                self.quiz["currentQuestion"] = {}
            self.quiz["currentQuestion"].update(payload)
        if not self.connected:
            self.lastEvent = (evt,payload)
        else:
            self.emit(evt,payload)

async def _proxy(options):
    pass
def _wsproxy(url):
    return url

client._defaults = {
    "modules": {
        "extraData": True,
        "feedback": True,
        "gameReset": True,
        "quizStart": True,
        "quizEnd": True,
        "podium": True,
        "timeOver": True,
        "reconnect": True,
        "questionReady": True,
        "questionStart": True,
        "questionEnd": True,
        "nameAccept": True,
        "teamAccept": True,
        "teamTalk": True,
        "backup": True,
        "answer": True
    },
    "proxy": _proxy,
    "wsproxy": _wsproxy,
    "options": {
        "ChallengeAutoContinue": True,
        "ChallengeGetFullScore": False,
        "ChallengeAlwaysCorrect": False,
        "ChallengeUseStreakBonus": False,
        "ChallengeWaitForInput": False,
        "ChallengeScore": None
    }
}
