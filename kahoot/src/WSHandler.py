import asyncio
import websocket
from . import consts
from pymitter import EventEmitter
from user_agent import generate_user_agent as UserAgent
import time
import math
from random import random as random
import json as JSON
try:
    import thread
except ImportError:
    import _thread as thread

class WSHandler(EventEmitter):
    def __init__(self,session,token,kahoot):
        super().__init__()
        self.requires2Step = False
        self.finished2Step = False
        self.kahoot = kahoot
        self.msgID = 0
        self.receivedQuestionTime = 0
        self.clientID = "_none_"
        self.connected = False
        self.gameID = session
        self.name = ""
        self.ready = False
        self.firstQuizEvent = False
        self.timesync = None
        self.lastReceivedQ = None
        def on_message(ws,m):
            self.message(m)
        def on_close(ws):
            #print("close")
            self.connected = False
            self.close()
        def on_error(ws,e):
            #print(e)
            self.connected = False
            self.emit("error",e)
            self.close()
        def on_open(ws):
            self.open(ws)
        self.ws = websocket.WebSocketApp(consts.WSS_ENDPOINT + str(session) + "/" + token,on_message=on_message,on_error=on_error,on_close=on_close)
        self.ws.on_open = on_open
        def _1(data,content):
            if not getattr(self.kahoot,"quiz"):
                self.emit("quizData",{
                    "name": None,
                    "type": content["quizType"],
                    "qCount": content["quizQuestionAnswers"][0],
                    "totalQ": len(content["quizQuestionAnswers"]),
                    "quizQuestionAnswers": content["quizQuestionAnswers"]
                })
            if not getattr(self.kahoot.quiz,"currentQuestion"):
                self.emit("quizUpdate", {
                    "questionIndex": content["questionIndex"],
                    "timeLeft": content["timeLeft"],
                    "type": content["gameBlockType"],
                    "useStoryBlocks": content.get("canAccessStoryBlocks"),
                    "ansMap": content.get("answerMap")
                })
            elif content["questionIndex"] > self.kahoot.quiz.currentQuestion.index:
                self.emit("quizUpdate", {
                    "questionIndex": content["questionIndex"],
                    "timeLeft": content["timeLeft"],
                    "type": content.get("gameBlockType"),
                    "useStoryBlocks": content.get("canAccessStoryBlocks"),
                    "ansMap": content.get("answerMap")
                })

        def _2(data,content):
            self.receivedQuestionTime = math.floor(time.time() * 1000)
            self.emit("questionStart")

        def _3(data,content):
            self.emit("finish", {
                "playerCount": content["playerCount"],
                "quizID": content["quizId"],
                "rank": content["rank"],
                "correct": content["correctCount"],
                "incorrect": content["incorrectCount"]
            })

        def _8(data,content):
            self.emit("questionEnd", {
                "correctAnswers": content["correctAnswers"],
                "correct": content["isCorrect"],
                "points": content["points"],
                "pointsData": content["pointsData"],
                "rank": content["rank"],
                "nemesis": content.get("nemesis"),
                "text": content.get("text"),
                "totalScore": content["totalScore"]
            })

        def _9(data,content):
            if not self.firstQuizEvent:
                self.firstQuizEvent = True
                self.emit("quizData", {
                    "name": content["quizName"],
                    "type": content.get("quizType"),
                    "qCount": content["quizQuestionAnswers"][0],
                    "totalQ": len(content["quizQuestionAnswers"]),
                    "quizQuestionAnswers": content["quizQuestionAnswers"]
                })

        def _10(data,content):
            self.emit("quizEnd")
            try:
                self.ws.close()
            except Exception as e:
                # probably already closed
                pass

        def _12(data,content):
            self.emit("feedback")

        def _13(data,content):
            self.emit("finishText", {
                "metal": content["podiumMedalType"]
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
            "1": _1,
            "2": _2,
            "3": _3,
            "8": _8,
            "9": _9,
            "10": _10,
            "12": _12,
            "13": _13,
            "51": _51,
            "52": _52,
            "53": _53
        }
    def getExt(self):
        return {
            ack: True,
            timesync: {
                l: 0,
                o: 0,
                tc: math.floor(time.time() * 1000)
            }
        }
    def getPacket(self, packet):
        l = None
        o = None
        try:
            l = round(((time.time() * 1000) - packet["ext"]["timesync"]["tc"] - packet["ext"]["timesync"]["p"]) / 2)
            o = packet["ext"]["timesync"]["ts"] - packet["ext"]["timesync"]["tc"] - l;
            self.timesync = {
                "tc": round(time.time() * 1000),
                "l": l,
                "o": o
            }
        except Exception as e:
            self.timesync = {
                "tc": round(time.time() * 1000),
                "l": 0,
                "o": 0
            }
        self.msgID+=1
        return [{
            "channel": packet["channel"],
            "clientId": self.clientID,
            "ext": {
                "ack": packet["ext"]["ack"],
                "timesync": {
                    "l": l,
                    "o": o,
                    "tc": round(time.time() * 1000)
                }
            },
            "id": str(self.msgID)
        }]
    def getSubmitPacket(self, questionChoice, question):
        self.msgID+=1
        r = [{
            "channel": "/service/controller",
            "clientId": self.clientID,
            "data": {
                "content": JSON.dumps({
                    "choice": questionChoice,
                    "questionIndex": self.kahoot.quiz.currentQuestion.index,
                    "meta": {
                        "lag": round(random() * 45 + 5)
                    },
                    "type": question.type
                }),
                "gameid": self.gameID,
                "host": consts.ENDPOINT_URI,
                "id": 45,
                "type": "message"
            },
            "id": str(self.msgID)
        }]
        if question.type == "open_ended" or question.type == "word_cloud":
            r[0].data.content = JSON.dumps({
                text: str(questionChoice),
                questionIndex: self.kahoot.quiz.currentQuestion.index,
                meta: {
                    lag: round(random() * 45 + 5)
                },
                type: question.type
            })
        elif question.type == "multiple_select_quiz" or question.type == "jumble":
            if type(questionChoice.append) != type(chr):
                r[0].data.content = JSON.dumps({
                    choice: [0,1,2,3],
                    questionIndex: self.kahoot.quiz.currentQuestion.index,
                    meta: {
                        lag: round(random() * 45 + 5)
                    },
                    type: question.type
                })
        return r
    def send(self, msg):
        if self.kahoot.loggingMode:
            print("SND: " + JSON.dumps(msg))
        if self.connected:
            try:
                self._ws.send(JSON.dumps(msg))
            except Exception as e:
                print(e)
                pass
    def sendSubmit(self, questionChoice, question, secret=None):
        timer = round(time.time() * 1000) - self.receivedQuestionTime
        if timer < 250:
            time.sleep(0.25 - (timer/1000))
        packet = self.getSubmitPacket(questionChoice,question)
        self.send(packet)
        self.emit("questionSubmit")
    def open(self,ws):
        self._ws = ws
        self.connected = True
        self.emit("open")
        r = [{
            "advice": {
                "interval": 0,
                "timeout": 60000
            },
            "channel": consts.CHANNEL_HANDSHAKE,
            "ext": {
                "ack": True,
                "timesync": {
                    "l": 0,
                    "o": 0,
                    "tc": round(time.time() * 1000)
                },
                "id": "1",
                "minimumVersion": "1.0",
                "supportedConnectionTypes": [
                    "websocket",
                    "long-polling"
                ],
                "version": "1.0"
            }
        }]
        self.msgID+=1
        self.send(r)
        pass
    def message(self, msg):
        if self.kahoot.loggingMode:
            print("DWN: " + msg)
        data = JSON.loads(msg)[0]
        if data.get("channel") == consts.CHANNEL_HANDSHAKE and data.get("error"):
            self.emit("error")
            self.close()
            return
        if data.get("channel") == consts.CHANNEL_HANDSHAKE and data.get("clientId"):
            self.clientID = data.get("clientId")
            r = self.getPacket(data)[0]
            r["advice"] = {
                "timeout": 0
            }
            r["channel"] = "/meta/connect"
            r["connectionType"] = "websocket"
            r["ext"]["ack"] = 0
            self.send([r])
        elif data.get("channel") == consts.CHANNEL_CONN and data.get("advice") and data.get("advice").get("reconnect") and data.get("advice").get("reconnect") == "retry":
            connectionPacket = {
                "ext": {
                    "ack": 1,
                    "timesync": self.timesync
                },
                "id": str(self.msgID + 1)
            }
            self.msgID += 1
            connectionPacket["channel"] = consts.CHANNEL_CONN
            connectionPacket["clientId"] = self.clientID
            connectionPacket["connectionType"] = "websocket"
            self.send([connectionPacket])
            time.sleep(0.5)
            self.ready = True
            self.emit("ready")
        elif data.get("data"):
            if data.get("data").get("error"):
                if data.get("data").get("type") and data.get("data").get("type") == "loginResponse":
                    return self.emit("invalidName",data["data"]["error"])
                try:
                    self.emit("error",data["data"]["error"])
                except Exception as e:
                    pass
                return
            elif data.get("data").get("type") == "loginResponse":
                self.kahoot.cid = data["data"]["cid"]
                self.emit("joined")
            elif data.get("data").get("type") == "status":
                if data["data"].get("status") == "LOCKED":
                    self.emit("locked")
                    self.close()
                    self.ws.close()
            else:
                if data.get("data").get("content"):
                    cont = JSON.loads(data.get("data").get("content"))
                    if self.dataHandler.get(str(data.get("data").get("id"))):
                        self.dataHandler.get(str(data["data"]["id"]))(data,cont)
        if data.get("ext") and data["channel"] == consts.CHANNEL_CONN and not data.get("advice") and self.ready:
            packet = self.getPacket(data)[0]
            packet["connectionType"] = "websocket"
            self.send([packet])
    def send2Step(self, steps):
        packet = [{
            "channel": "/service/controller",
            "clientId": self.clientID,
            "data": {
                "id": 50,
                "type": "message",
                "gameid": self.gameID,
                "host": consts.ENDPOINT_URI,
                "content": JSON.dumps({
                    "sequence": steps
                })
            },
            "id": str(self.msgID)
        }]
        self.msgID+=1
        self.send(packet)
    def sendFeedback(self, fun, learning, recommend, overall):
        packet = [{
            "channel": "/service/controller",
            "clientId": self.clientID,
            "data": {
                "id": 11,
                "type": "message",
                "gameid": self.gameID,
                "host": consts.ENDPOINT_URI,
                "content": JSON.stringify({
                    "totalScore": self.kahoot.totalScore,
                    "fun": fun,
                    "learning": learning,
                    "recommend": recommend,
                    "overall": overall,
                    "nickname": self.kahoot.name
                })
            },
            "id": str(self.msgID)
        }]
        self.msgID += 1
        time.sleep(1)
        self.send(packet)
    def relog(self, cid):
        if not self.ready:
            time.sleep(0.5)
            self.relog(cid)
            return
        self.msgID += 1
        packet = {
            "channel": "/service/controller",
            "clientId": self.clientID,
            "data": {
                "cid": cid,
                "content": JSON.dumps({
                    "device": {
                        "userAgent": UserAgent(),
                        "screen": {
                            "width": 2000,
                            "height": 1000
                        }
                    }
                }),
                "gameid": self.gameID,
                "host": "kahoot.it",
                "type": "relogin"
            },
            "ext": {},
            "id": str(self.msgID)
        }
        self.send([packet])
    def login(self, name, team):
        if not self.ready:
            time.sleep(0.5)
            self.login(name,team)
            return
        self.name = name
        self.msgID+=1
        joinPacket = [{
            "channel": "/service/controller",
            "clientId": self.clientID,
            "data": {
                "content": '{"device":{"userAgent":"' + UserAgent() + '","screen":{"width":1280,"height":800}}}',
                "gameid": self.gameID,
                "host": consts.ENDPOINT_URI,
                "name": self.name,
                "type": "login"
            },
            "ext": {},
            "participantUserId": None,
            "id": str(self.msgID)
        }]
        time.sleep(0.5)
        self.send(joinPacket)
        if self.kahoot.gamemode == "team":
            joinPacket2 = [{
                "channel": "/service/controller",
                "clientId": self.clientID,
                "data": {
                    "content": JSON.dumps(team if type(team) == type(list()) else team if len(team) else ["Player 1", "Player 2", "Player 3", "Player 4"]),
                    "gameid": self.gameID,
                    "host": consts.ENDPOINT_URI,
                    "id": 18,
                    "type": "message"
                },
                "ext": {},
                "participantUserId": None,
                "id": str(self.msgID)
            }]
            self.msgID+=1
            time.sleep(0.5)
            self.send(joinPacket2)
    def close(self):
        self.connected = False
        self.ws.close()
        self.emit("close")
    def leave(self):
        self.msgID+=1
        try:
            self.timesync["tc"] = round(time.time() * 1000)
        except:
            pass
        self.send([{
            "channel": "/meta/disconnect",
            "clientId": self.clientID,
            "ext": {
                "timesync": self.timesync
            },
            "id": str(self.msgID)
        }])
        time.sleep(0.5)
        self.close()
