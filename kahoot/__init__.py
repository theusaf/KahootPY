from pymitter import EventEmitter
from .src import token
from .src import Assets
from .src import WSHandler
from .src import ChallengeHandler
from .src import consts

class client(EventEmitter):
    def __init__(self,proxies,options):
        self._wsHandler = None
        self.token = None
        self.sessionID = None
        self.name = None
        self.quiz = None
        self.totalScore = 0
        self.gamemode = None
        self.cid = ""
        self.proxies = proxies
        self.loggingMode = False
        self.joined = False
        self.options = {
            ChallengeAutoContinue: True,
            ChallengeGetFullScore: False
        }.update(options)
    async def reconnect():
        if self.sessionID and this.cid and this._wsHandler and this._wsHandler.ws.open:
            if self.sessionID[0] == "0":
                return
            def _(resolvedToken,content):
                pass
            await token.resolve(self.sessionID,_,self.proxies)
        pass
    async def join(pin,name,team):
        pass
    def answer2Step(steps):
        pass
    def answerQuestion(arg):
        pass
    def leave():
        pass
    def sendFeedback(fun,learning,recommend,overall):
        pass
    def next():
        pass

def _defineListeners(client):
    pass
