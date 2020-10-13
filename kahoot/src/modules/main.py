from ..assets.LiveClientHandshake import LiveClientHandshake
from ..assets.LiveJoinPacket import LiveJoinPacket
from ..assets.LiveJoinTeamPacket import LiveJoinTeamPacket
from ..assets.LiveTwoStepAnswer import LiveTwoStepAnswer
from ..assets.LiveLeavePacket import LiveLeavePacket
import time
import math
import json

def main(self):
    self.classes["LiveTwoStepAnswer"] = LiveTwoStepAnswer
    self.classes["LiveJoinPacket"] = LiveJoinPacket
    self.classes["LiveClientHandshake"] = LiveClientHandshake
    self.classes["LiveJoinTeamPacket"] = LiveJoinTeamPacket
    def HandshakeChecker(message):
        if message["channel"] == "/meta/handshake":
            if message.get("clientId"):
                self.clientId = message["clientId"]
                serverTime = message["ext"]["timesync"]
                l = math.round((int(time.time() * 1000) - serverTime["tc"] - serverTime["p"]) / 2)
                o = serverTime["ts"] - serverTime["tc"] - l
                def tc():
                    return int(time.time() * 1000)
                self._timesyncs = {
                    "l": l,
                    "o": o,
                    "tc": property(tc)
                }
                self._send(LiveClientHandshake(1,self._timesync,self))
                del self.handlers["HandshakeChecker"]
            else:
                self.emit("HandshakeFailed",message)
                try:
                    self.socket.close()
                except Exception:
                    pass
    self.handlers.HandshakeChecker = HandshakeChecker

    def PingChecker(message):
        if message["channel"] == "/meta/connect" and message.get("ext"):
            if message.get("advice") and message["advice"].get("reconnect") == "retry":
                self.emit("HandshakeComplete")
            self._send(LiveClientHandshake(2,message,self))
    self.handlers["PingChecker"] = PingChecker

    def timetrack(message):
        if self.waiting:
            if self.waiting.get(message["id"]):
                self.waiting[message["id"]](message)
                del self.waiting[message["id"]]
    self.handlers["timetrack"] = timetrack

    def TwoFactor(message):
        if self.settings and not self.settings["twoFactorAuth"]:
            del self.handlers.get("TwoFactor")
        if message["channel"] == "/service/player" and message.get("data"):
            if message["data"].get("id") == 53:
                self.twoFactorResetTime = int(time.time() * 1000)
                self.emit("TwoFactorReset")
            elif message["data"].get("id") == 51:
                self.emit("TwoFactorWrong")
            elif message["data"].get("id") == 52:
                self.connected = True
                self.emit("TwoFactorCorrect")
                if self.lastEvent:
                    self.emit(self.lastEvent[0],self.lastEvent[1])
                self.lastEvent = None
                self.twoFactorResetTime = None
                del self.handlers["TwoFactor"]
    self.handlers["TwoFactor"] = TwoFactor

    def Disconnect(message):
        if message["channel"] == "/service/player" and message.get("data") and message["data"].get("id") == 10:
            content = json.loads(message["data"]["content"])
            if content["kickCode"]:
                self.disconnectReason = "Kicked"
            else:
                self.disconnectReason = "Session Ended"
            self.leave(True)
    self.handlers["Disconnect"] = Disconnect
