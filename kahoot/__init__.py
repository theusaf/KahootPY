from pymitter import EventEmitter
from .src import token
from .src import Assets
from .src.WSHandler import WSHandler
# from .src.ChallengeHandler import ChallengeHandler
from .src import consts
import threading
import time

class client(EventEmitter):
    def __init__(self,proxies={},options={}):
        super().__init__()
        self._wsHandler = None
        self.token = None
        self.sessionID = None
        self.name = None
        self.team = []
        self.quiz = None
        self.totalScore = 0
        self.gamemode = None
        self.hasTwoFactorAuth = False
        self.usesNamerator = False
        self.cid = ""
        self.proxies = proxies
        self.loggingMode = False
        self.joined = False
        self.options = {
            "ChallengeAutoContinue": True,
            "ChallengeGetFullScore": False
        }.update(options)
    def reconnect(self):
        if self.sessionID and this.cid and this._wsHandler and this._wsHandler.ws.open:
            if self.sessionID[0] == "0":
                return False
            def _(resolvedToken,gamemode):
                self.gamemode = content.get("gameMode") or "classic"
                self.hasTwoFactorAuth = content.get("twoFactorAuth") or False
                self.usesNamerator = content.get("namerator") or False
                self.token = resolvedToken
                self._wsHandler = WSHandler(self.sessionID,self.token,self)
                _defineListeners(self,self._wsHandler)
                thread.start()
            try:
                content = token.resolve(self.sessionID,self.proxies)
            except Exception:
                return False
            return True
    def join(self,pin,name,team=["Player 1","Player 2","Player 3","Player 4"]):
        if not pin or not name:
            return False
        self.sessionID = pin
        self.name = name
        self.team = team
        def _(resolvedToken,content):
            if(resolvedToken == True):
                print("Challenges are not supported by KahootPY yet.")
                return False
            self.gamemode = content.get("gameMode") or "classic"
            self.hasTwoFactorAuth = content.get("twoFactorAuth") or False
            self.usesNamerator = content.get("namerator") or False
            self.token = resolvedToken
            self._wsHandler = WSHandler(self.sessionID,self.token,self)
            _defineListeners(self,self._wsHandler)
            thread = threading.Thread(target=self._wsHandler.ws.run_forever)
            thread.start()
        try:
            content = token.resolve(self.sessionID,_,self.proxies)
        except Exception:
            return False
    def answer2Step(self,steps):
        self._wsHandler.send2Step(steps)
    def answerQuestion(self,id,question,secret={}):
        if not question:
            question = self.quiz.currentQuestion
        self._wsHandler.sendSubmit(id,question,secret)
    def leave(self):
        self._wsHandler.leave()
    def sendFeedback(self,fun=1,learning=1,recommend=1,overall=5):
        self._wsHandler.sendFeedback(fun,learning,recommend,overall)
    def next(self):
        if self.gamemode == "challenge":
            self._wsHandler.next()
            return True
        return False
def _defineListeners(client,socket):
    def errorHandle(e):
        client.emit("handshakeFailed",e)
    def invalidNameHandle(err):
        client.emit("invalidName",err)
    def TwoFailHandle():
        client.emit("2StepFail")
    def TwoSuccessHandle():
        client.emit("2StepSuccess")
    def TwoHandle():
        client.emit("2Step")
    def ReadyHandle():
        socket.login(client.name,client.team)
    def JoinHandle():
        client.emit("ready")
        client.emit("joined")
        if client.hasTwoFactorAuth:
            client.emit("2Step")
    def QuizDataHandle(quizInfo):
        client.quiz = Assets.Quiz(quizInfo.get("name"),quizInfo["type"],quizInfo.get("qCount"),client,quizInfo["totalQ"],quizInfo["quizQuestionAnswers"],quizInfo)
        client.emit("quizStart",client.quiz)
        client.emit("quiz",client.quiz)
    def QuizUpdateHandle(updateInfo):
        client.quiz.currentQuestion = Assets.Question(updateInfo,client)
        client.emit("question",client.quiz.currentQuestion)
    def QuestionEndHandle(endInfo):
        e = Assets.QuestionEndEvent(endInfo,client)
        client.totalScore = e.total
        client.emit("questionEnd",e)
    def QuizEndHandle():
        client.emit("quizEnd")
        client.emit("disconnect")
    def QuestionStartHandle():
        try:
            client.emit("questionStart",client.quiz.currentQuestion)
        except Exception as e:
            # likely joined during quiz
            pass
    def QuestionSubmitHandle(message=None):
        e = Assets.QuestionSubmitEvent(message,client)
        client.emit("questionSubmit",e)
    def FinishTextHandle(data):
        e = Assets.FinishTextEvent(data)
        client.emit("finishText",e)
    def FinishHandle(data):
        e = Assets.QuizFinishEvent(data,client)
        client.emit("finish",e)
    def FeedbackHandle():
        client.emit("feedback")
    def LockedHandle():
        client.emit("locked")
    socket.on("error",errorHandle)
    socket.on("invalidName",invalidNameHandle)
    socket.on("locked",LockedHandle)
    socket.on("2StepFail",TwoFailHandle)
    socket.on("2StepSuccess",TwoSuccessHandle)
    socket.on("2Step",TwoHandle)
    socket.on("ready",ReadyHandle)
    socket.on("joined",JoinHandle)
    socket.on("quizData",QuizDataHandle)
    socket.on("quizUpdate",QuizUpdateHandle)
    socket.on("questionEnd",QuestionEndHandle)
    socket.on("quizEnd",QuizEndHandle)
    socket.on("questionStart",QuestionStartHandle)
    socket.on("questionSubmit",QuestionSubmitHandle)
    socket.on("finishText",FinishTextHandle)
    socket.on("finish",FinishHandle)
    socket.on("feedback",FeedbackHandle)
