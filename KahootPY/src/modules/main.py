from ..assets.LiveJoinPacket import LiveJoinPacket
from ..assets.LiveJoinTeamPacket import LiveJoinTeamPacket
from ..assets.LiveTwoStepAnswer import LiveTwoStepAnswer
import time
import math
import json

def main(self):
    self.classes["LiveTwoStepAnswer"] = LiveTwoStepAnswer
    self.classes["LiveJoinPacket"] = LiveJoinPacket
    self.classes["LiveJoinTeamPacket"] = LiveJoinTeamPacket

    def TwoFactor(message):
        if message["channel"] == "/service/player" and message.get("data") and not self.connected:
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
