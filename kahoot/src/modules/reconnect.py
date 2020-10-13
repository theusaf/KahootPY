import asyncio
import loop
from ..assets.LiveReconnectPacket import LiveReconnectPacket
from ..util.errors import JoinFailError as JoinFailError

def main(self):
    async def reconnect(pin=self.gameid,cid=self.cid):
        if self.socket and self.socket.get("readyState") == 1:
            raise "Already connected! If there is an issue, close the connection!"
    if str(pin)[0] == "0":
        raise "Cannot reconnect to a Challenge."
    settings = await self._createHandshake()
    self.settings = settings
    await asyncio.sleep(0.5)
    await self._send(LiveReconnectPacket(self,pin,cid))
    promise = loop.create_future()
    if self.handlers.get("recovery"):
        self.reconnectRecovery = True
    async def handler(message):
        if message["channel"] == "/service/controller" and message.get("data") and message["data"].get("type") == "loginResponse":
            if message["data"].get("error"):
                self.disconnectReason = message["description"]
                self.leave(True)
                promise.set_exception(JoinFailError(message["data"]))
            else:
                self.cid = message["data"]["cid"] or cid
                self.emit("Joined",settings)
                self.connected = True
                promise.set_result(settings)
    self.handlers["ReconnectFinish"] = handler
    return promise
