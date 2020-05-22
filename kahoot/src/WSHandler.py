import asyncio
import websocket
import ssl
from . import consts
from pymitter import EventEmitter
from user_agent import generate_user_agent as UserAgent
import base64
import time
import math

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

class WSHandler(EventEmitter):
    def __init__(self,session,token,kahoot):
        super().__init__()
        self.requires2Step = False;
		self.finished2Step = False;
		self.kahoot = kahoot;
		self.msgID = 0;
		self.receivedQuestionTime = 0;
		self.clientID = "_none_";
		self.connected = False;
		self.gameID = session;
		self.name = "";
		self.firstQuizEvent = False;
		self.lastReceivedQ = None;
        def on_message(m):
            self.message(m)
        def on_close():
            self.connected = False
            self.close()
        def on_error(e):
            self.connected = False
            self.emit("error",e)
            self.close()
        def on_open():
            self.open()
        self.ws = websocket.WebSocketApp()
        self.ws.connect(consts.WSS_ENDPOINT + session + "/" + token,on_message=on_message,on_error=on_error,on_close=on_close,sslopt={"check_hostname": False})
        self.ws.on_open = on_open
        self.ws.run_forever()
        def _1(data,content):
            if not self.kahoot.quiz:
                self.emit("quizData",{
                    name: None,
                    type: content.quizType,
                    qCount: content.quizQuestionAnswers[0],
                    totalQ: content.quizQuestionAnswers.length,
                    quizQuestionAnswers: content.quizQuestionAnswers
                })
            if not self.kahoot.quiz.currentQuestion:
                self.emit("quizUpdate", {
                    questionIndex: content.questionIndex,
                    timeLeft: content.timeLeft,
                    type: content.gameBlockType,
                    useStoryBlocks: content.canAccessStoryBlocks,
                    ansMap: content.answerMap
                })
            elif content.questionIndex > self.kahoot.quiz.currentQuestion.index:
                self.emit("quizUpdate", {
                    questionIndex: content.questionIndex,
                    timeLeft: content.timeLeft,
                    type: content.gameBlockType,
                    useStoryBlocks: content.canAccessStoryBlocks,
                    ansMap: content.answerMap
                });

        def _2(data,content):
            self.receivedQuestionTime = math.floor(time.time())
            self.emit("questionStart")

        def _3(data,content):
            self.emit("finish", {
                playerCount: content.playerCount,
                quizID: content.quizId,
                rank: content.rank,
                correct: content.correctCount,
                incorrect: content.incorrectCount
            })

        def _8(data,content):
            self.emit("questionEnd", {
                correctAnswers: content.correctAnswers,
                correct: content.isCorrect,
                points: content.points,
                pointsData: content.pointsData,
                rank: content.rank,
                nemesis: content.nemesis,
                text: content.text,
                totalScore: content.totalScore
            });

        def _9(data,content):
            if not self.firstQuizEvent:
                self.firstQuizEvent = True
                self.emit("quizData", {
                    name: content.quizName,
                    type: content.quizType,
                    qCount: content.quizQuestionAnswers[0],
                    totalQ: content.quizQuestionAnswers.length,
                    quizQuestionAnswers: content.quizQuestionAnswers
                })

        def _10(data,content):
            self.emit("quizEnd")
            try:
                self.ws.close()
            except CloseSocketError as e:
                # probably already closed
                pass

        def _12(data,content):
            self.emit("feedback")

        def _13(data,content):
            self.emit("finishText", {
                metal: content.podiumMedalType
            })

        def _51(data,content):
            self.emit("2StepFail")

        def _52(data,content):
            if not self.finished2Step:
                self.finished2Step = True
                self.emit("2StepSuccess")

        def _53(data,content):
            self.requires2Step = True
            if not self.finished2Step:
                self.emit("2Step")

        self.dataHandler = {
            1: _1,
            2: _2,
            3: _3,
            8: _8,
            9: _9
            10: _10,
            12: _12,
            13: _13,
            51: _51,
            52: _52,
            53: _53
        }
