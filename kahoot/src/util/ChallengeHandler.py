from pymitter import EventEmitter
import requests
import time
import copy
import json as JSON
import math
import asyncio
import re
import threading
import urllib
import copy
import .errors
import loop
from .emoji import regex as emoji

invalid = re.compile(r"[~`!@#$%^&*(){}[\];:\"'<,.>?/\\|\-_+=]",re.M)

def Injector(self):
    self.data = self.data or {}
    self.stop = False
    self.data.update({
        "totalScore": 0,
        "totalScoreNoBonus": 0,
        "totalStreak": 0,
        "streak": -1,
        "phase": "start",
        "questionIndex": 0,
        "correctCount": 0,
        "incorrectCount": 0,
        "unansweredCount": 0
    })

    async def answer(choice,empty):
        try:
            self.ti.cancel()
        except Exception:
            pass
        question = self.challengeData["kahoot"]["questions"][self.data["questionIndex"]]
        tick = time.time() * 1000 - self.receivedQuestionTime
        if self.defaults["options"]["ChallengeGetFullScore"] or self.defaults["options"]["ChallengeWaitForInput"] or not self.challengeData["challenge"]["game_options"]["question_timer"]:
            tick = 1
        pqc = copy.copy(self.challengeData["progress"]["questions"])
        pqc.reverse()
        pointsQuestion = pqc[0]["pointsQuestion"] or False
        if int(self.defaults["options"]["ChallengeScore"] > 1500):
            self.defaults["options"]["ChallengeScore"] = 1500
        else if int(self.defaults["options"]["ChallengeScore"] < 0):
            self.defaults["options"]["ChallengeScore"] = 0
        timeScore = int(self.defaults["options"]["ChallengeScore"]) or (math.round((1-(tick/question.get("time"))/2)) * 1000) * question.get("pointsMultiplier") * int(pointsQuestion)
        if self.data["streak"] == -1:
            self.data["streak"] = 0
            ent = self.challengeData["progress"]["playerProgress"]["playerProgressEntries"]
            falseScore = 0
            for q in ent:
                if q >= self.data["questionIndex"]:
                    break
                if not ent[q]["questionMetrics"]:
                    break
                if ent[q]["questionMetrics"].get(self.name) > falseScore or not self.challengeData["kahoot"]["questions"][q].get("points"):
                    self.data["streak"] = self.data["streak"] + 1
                else:
                    self.data["streak"] = 0
                falseScore = ent[q]["questionMetrics"].get(self.name)
                self.data["score"] = falseScore
            alwaysCorrect = self.defaults["options"]["ChallengeAlwaysCorrect"]
            correct = False
            text = ""
            if empty is None:
                choice = -1
            choiceIndex = int(choice)
            c2 = []
            score = 0
            qtype = question["type"]
            if qtype == "quiz":
                try:
                    correct = question["choices"][choiceIndex]["correct"]
                    text = question["choices"][choiceIndex]["answer"]
                except Exception:
                    correct = False
                    text = ""
                finally:
                    if alwaysCorrect:
                        correct = True
                    if correct:
                        score = score + timeScore
            elif qtype == "jumble":
                correct = JSON.dumps(choice) == JSON.dumps([0,1,2,3])
                if not isinstance(choice,list):
                    choice = []
                for j in choice:
                    choice[j] = int(choice[j])
                tmpList = []
                for n in choice:
                    try:
                        tmpList.append(question["choices"][choice[n]]["answer"])
                    except Exception:
                        tmpList.append("")
                text = "|".join(tmpList)
                choiceIndex = -1
                if alwaysCorrect:
                    correct = True
                if correct:
                    score = score + timeScore
            elif qtype == "multiple_select_quiz":
                if not isinstance(choice,list):
                    choice = []
                correct = True
                for i in choice:
                    choice[i] = int(choice[i])
                for ch in question["choices"]:
                    if question["choices"][ch]["correct"]:
                        c2.append(ch)
                        if int(ch) in choice or alwaysCorrect:
                            if correct:
                                score = score + timeScore
                        else:
                            score = 0
                            correct = False
            elif qtype == "open_ended":
                text = str(choice)
                test = invalid.sub("",text)
                for i in question["choices"]:
                    choice = question["choices"][i]
                    if emoji.sub("",choice["answer"]):
                        correct = emoji.sub("",test).lower() == invalid.sub("",emoji.sub("",choice["answer"])).lower()
                    else:
                        correct = test == choice
                    if correct:
                        choiceIndex = question["choices"].index(choice)
                        break
                if alwaysCorrect:
                    correct = True
                if correct:
                    score = score + timeScore
            elif qtype == "word_cloud":
                text = str(choice)
                choiceIndex = -1
                correct = True
                if self.defaults["options"]["ChallengeScore"]:
                    score = score + timeScore
            else:
                choiceIndex = int(choice) or 0
                correct = True
                if self.defaults["options"]["ChallengeScore"]:
                    score = score + timeScore
            c = []
            if question.get("choices"):
                for i in question["choices"]:
                    choice = question["choices"][i]
                    if choice["correct"]:
                        c.push(choice["answer"])
            oldstreak = self.data["streak"]
            if correct:
                self.data["streak"] = self.data["streak"] + 1
            else:
                self.data["streak"] = 0
            payload = {
                "device": {
                    "screen": {
                        "width": 1920,
                        "height": 1080
                    },
                    "userAgent": self.userAgent
                },
                "gameMode": self.challengeData["progress"].get("gameMode"),
                "gameOptions": self.challengeData["progress"]["gameOptions"],
                "hostOriganizationId": None,
                "kickedPlayers": [],
                "numQuestions": len(self.challengeData["kahoot"]["questions"]),
                "organizationId": "",
                "question": {
                    "answers": [
                        {
                            "bonusPoints": {
                                "answerStreakBonus": self._calculateStreakBonus()
                            },
                            "choiceIndex": choiceIndex,
                            "isCorrect": correct,
                            "playerCid": int(self.cid),
                            "playerId": self.name,
                            "points": int(correct) * score,
                            "reactionTime": tick,
                            "receivedTime": time.time() * 1000,
                            "text": text
                        }
                    ],
                    "choices": question.get("choices"),
                    "duration": question.get("time"),
                    "format": question.get("questionFormat"),
                    "index": self.data["questionIndex"],
                    "lag": 0,
                    "layout": question.get("layout"),
                    "playerCount": 1,
                    "pointsQuestion": pointsQuestion,
                    "skipped": empty is None,
                    "startTime": self.receivedQuestionTime,
                    "title": question.get("question"),
                    "type": question["type"],
                    "video": question.get("video")
                },
                "quizId": self.challengeData["kahoot"]["uuid"],
                "quizMaster": self.challengeData["challenge"].get("quizMaster"),
                "quizTitle": self.challengeData["kahoot"]["title"],
                "quizType": self.challengeData["progress"].get("quizType"),
                "sessionId": self.gameid,
                "startTime": self.challengeData["progress"]["timestamp"]
            }

            if qtype == "word_cloud" or qtype == "open_ended":
                payload["question"]["answers"][0].update({
                    "originalText": text,
                    "text": invalid.sub("",text.lower())
                })
                payload["question"]["choices"] = []
            elif qtype == "jumble":
                f = choice
                if len(f) != 4:
                    f = [3,2,1,0]
                payload["question"]["answers"][0]["selectedJumbleOrder"] = f
            elif qtype == "multiple_select_quiz":
                payload["question"]["answers"][0]["selectedChoices"] = choice
                payload["question"]["answers"][0]["choiceIndex"] = -5
            elif qtype == "content":
                payload["question"]["answers"][0].update({
                    "choiceIndex": -2,
                    "isCorrect": True,
                    "reactionTime": 0
                })
            oldScore = score
            score = score + payload["question"]["answers"][0]["bonusPoints"]["answerStreakBonus"]
            self.data["totalStreak"] = self.data["totalScore"] + score - oldScore
            self.data["totalScoreNoBonus"] = self.data["totalScoreNoBonus"] + oldScore
            self.data["totalScore"] = self.data["totalScore"] + score
            if correct:
                self.data["correctCount"] = self.data["correctCount"] + 1
            if not correct and empty is None:
                self.data["unansweredCount"] = self.data["unansweredCount"] + 1
            if not correct and not (empty is None):
                self.data["incorrectCount"] = self.data["incorrectCount"] + 1
            event = {
                "choice": choice,
                "type": qtype,
                "isCorrect": correct,
                "text": text,
                "receivedTime": time.time() * 1000,
                "pointsQuestion": pointsQuestion,
                "points": score,
                "correctAnswers": c,
                "correctChoices": c2,
                "totalScore": self.data["totalScore"],
                "rank": self._getRank(),
                "nemesis": self._getNemesis(),
                "pointsData": {
                    "questionPoints": oldScore,
                    "totalPointsWithBonuses": self.data["totalScore"],
                    "totalPointsWithoutBonuses": self.data["totalScoreNoBonus"],
                    "answerStreakPoints": {
                        "streakLevel": (correct and self.data["streak"]) or 0,
                        "streakBonus": self._calculateStreakBonus(),
                        "totalStreakPoints": self.data["totalStreak"],
                        "previousStreakLevel": oldstreak,
                        "previousStreakLevel": self._calculateStreakBonus(oldstreak)
                    }
                }
            }
            self.data["finalResult"] = {
                "rank": event["rank"],
                "cid": self.cid,
                "correctCount": self.data["correctCount"],
                "incorrectCount": self.data["incorrectCount"],
                "unansweredCount": self.data["unansweredCount"],
                "isKicked": False,
                "isGhost": False,
                "playerCount": len(self.challengeData["challenge"]["challengeUsersList"]) + 1,
                "startTime": self.challengeData["progress"]["timestamp"],
                "quizId": self.challengeData["kahoot"]["uuid"],
                "name": self.name,
                "totalScore": self.data["totalScore"],
                "hostId": "",
                "challengeId": "",
                "isOnlyNonPointGameBlockKahoot": False
            }
            data = await self._httpRequest(f"https://kahoot.it/rest/challenges/{self.challengeData["challenge"]["challengeId"]}/answers",{
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Length": len(JSON.dumps(payload).encode("utf-8"))
                },
                "method": "POST"
            },false,JSON.dumps(payload))
            if empty is None:
                return event
            def waiter():
                self._emit("TimeOver")
                self._emit("QuestionEnd",event)
                self.next()
            self.ti = threading.Timer(1,waiter)
            self.ti.start()

    self.answer = answer

    async def next():
        if self.stop:
            return
        phase = self.data["phase"]
        if phase == "start":
            self.data["phase"] = "ready"
            kahoot = self.challengeData["kahoot"]
            qqa = []
            for i in kahoot["questions"]:
                question = kahoot["questions"][i]
                qqa.append(len(question["choices"]) if question.get("chioces") else None)
            self._emit("QuizStart",{
                "name": kahoot.get("title"),
                "quizQuestionAnswers": qqa
            })
            def waiter():
                self.next()
            t = threading.Timer(5,waiter)
            t.start()
        elif phase == "ready":
            try:
                inf = await this._getProgress(self.data["questionIndex"])
                if self.data.get("hitError") == True:
                    self.data["hitError"] = False
                if len(inf) != 0:
                    self.challengeData["progress"] = inf
                self.data.phase = "answer"
                q = self.challengeData["kahoot"]["questions"][self.data["questionIndex"]]
                q.update({
                    "questionIndex": self.data["questionIndex"],
                    "timeLeft": 5,
                    "gameBlockType": q["type"],
                    "gameBlockType": q.get("layout"),
                    "quizQuestionAnswers": self.quiz["quizQuestionAnswers"]
                })
                self.emit("QuestionReady",q)
                def waiter():
                    self.next()
                t = threading.Timer(5,waiter)
                t.start()
            except Exception:
                if self.data.get("hitError"):
                    try:
                        self.ti.cancel()
                    except Exception:
                        pass
                    self.disconnectReason = "Kahoot - Internal Server Error"
                    try:
                        self.socket.close()
                    except Exception:
                        pass
                self.data["hitError"] = True
                self.next()
        elif phase == "answer":
            q = self.challengeData["kahoot"]["questions"][self.data["questionIndex"]]
            self.receivedQuestionTime = time.time() * 1000
            self.data["phase"] = "leaderboard"
            if not q:
                self.disconnectReason = "Unknown Error"
                try:
                    self.socket.close()
                except Exception:
                    pass
                return
            if q["type"] == "content":
                self.data["questionIndex"] = self.data["questionIndex"] + 1
                self.data["phase"] = "ready"
                if self.data["questionIndex"] == len(self.challengeData["kahoot"]["questions"][self.data["questionIndex"]]):
                    self.data["phase"] = "close"
                if self.challengeData["challenge"]["game_options"]["question_timer"] and not self.defaults["options"]["ChallengeWaitForInput"]:
                    def waiter():
                        self.next()
                    t = threading.Timer(10,waiter)
                    t.start()
                return
            if self.challengeData["challenge"]["game_options"]["question_timer"] and not self.defaults["options"]["ChallengeWaitForInput"]:
                async def waiter():
                    evt = await self.answer(None,None)
                    if q["type"] != "content":
                        self._emit("TimeOver")
                        self._emit("QuestionEnd",evt)
                    self.next()
                self.ti = threading.Timer((q["time"] / 1000) or 5,waiter)
                self.ti.start()
                return
            q.update({
                "questionIndex": self.data["questionIndex"],
                "gameBlockType": q["type"],
                "gameBlockLayout": q["layout"],
                "quizQuestionAnswers": self.quiz["quizQuestionAnswers"],
                "timeAvailable": q["time"]
            })
            self._emit("QuestionStart",q)
        elif phase == "leaderboard":
            self.data["questionIndex"] = self.data["questionIndex"] + 1
            self.data["phase"] = "ready"
            if self.data["questionIndex"] == len(self.challengeData.kahoot.questions):
                self.data["phase"] = "close"
                if self.defaults["options"]["ChallengeAutoContinue"]:
                    def waiter():
                        self.next()
                    t = threading.Timer(5,waiter)
                    t.start()
                return
            if self.defaults["options"]["ChallengeAutoContinue"]:
                def waiter():
                    self.next()
                t = threading.Timer(5,waiter)
                t.start()
        elif phase == "close":
            self.data["phase"] = "complete"
            self._emit("QuizEnd",self.data["finalResult"])
            self._emit("Podium",{
                "podiumMedalType": ["gold","silver","bronze"][self._getRank() - 1] if self._getRank() <= 3 else None
            })
            if self.defaults["options"]["ChallengeAutoContinue"]:
                def waiter():
                    self.next()
                t = threading.Timer(30,waiter)
                t.start()
        elif phase == "complete":
            self.stop = True
            self.disconnectReason = "Session Ended"
            try:
                self.socket.close()
            except Exception:
                pass

    self.next = next

    def leave():
        self.stop = True
        self.disconnectReason = "Player Left"
        try:
            self.socket.close()
        except Exception:
            pass

    self.leave = leave

    def joined(cid):
        self.socket.on_message(JSON.dumps([
            {
                "channel": "/service/controller",
                "data": {
                    "type": "loginResponse",
                    "cid": str(cid)
                }
            }
        ]))
        t = threading.Timer(0.1,waiter)
        t.start()

        def _send():
            raise "This error should not appear unless you are trying to do something silly."
        self._send = _send

    def _calculateStreakBonus(info = self.data["streak"]):
        if self.defaults["options"]["ChallengeUseStreakBonus"]:
            if info >= 6:
                return 500
            elif info > 0:
                return (info - 1) * 100
            else:
                return 0
        else:
            return 0

    self._calculateStreakBonus = _calculateStreakBonus

    async def _send(m):
        if m.get("data") and m["data"].get("type") == "login":
            self.name = str(m["data"]["name"])

            data = await self._httpRequest(f"https://kahoot.it/rest/challenges/{self.challengeData["challenge"]["challengeId"]}/join/?nickname={urllib.parse.quote(self.name)}",{
                "method": "POST"
            },True)
            if data.get("error"):
                raise JoinFailError(data)
            self.challengeData.update(data)
            self.cid = data["playerCid"]
            joined(self.cid)
            if self.defaults["options"]["ChallengeAutoContinue"]:
                def waiter():
                    self.next()
                t = threading.Timer(5,waiter)
                t.start()
            return self.challengeData

    self._send = _send

    def _httpRequest(url,opts={},json=None,packet=None):
        parsed = urllib.parse.urlparse(url)
        options = {
            "headers": {
                "User-Agent": self.userAgent,
                "Origin": "kahoot.it",
                "Referer": "https://kahoot.it/",
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*"
            },
            "host": parsed.netloc,
            "protocol": f"{parsed.scheme}:",
            "path": parsed.path + parsed.query
        }
        for i in opts:
            if isinstance(opts[i],dict):
                if not options.get(i):
                    options[i] = opts[i]
                else:
                    options[i].update(opts[i])
            else:
                options[i] = opts[i]
        proxyOptions = self.defaults["proxy"](options)
        r = None
        if proxyOptions.get("headers") and proxyOptions.get("text"):
            # Proxied request
            r = proxyOptions
            def json():
                return JSON.loads(r["text"])
            r.json = json
        else:
            if proxyOptions:
                options.update(proxyOptions)
            url = (options.get("protocol") or "https:") + "//" + (options.get("host") or options.get("host")) + (options.get("port") or "") + options.get("path")
            r = requests.request(options.get("method") or "GET",url,headers=options.get("headers"),json=JSON.loads(packet) if json else None)
        try:
            if json:
                return r.json()
            else:
                return r.text
        except Exception:
            raise ValueError(r.text)

        if json and self.loggingMode:
            print("SEND: " + packet)

    self._httpRequest = _httpRequest

    def _getNemesis():
        if not self.challengeData["progress"]["playerProgress"]:
            return None
        scores = copy.copy(self.challengeData["progress"]["playerProgress"]["playerProgressEntries"])
        scores.reverse()
        latest = scores[0].questionMetrics
        rank = 0
        name = None
        totalScore = None
        for i in latest:
            if i == self.name:
                continue
            if latest[i] >= self.data["totalScore"]:
                rank = rank + 1
                if latest[i] < totalScore or name is None:
                    name = i
                    totalScore = latest[i]
        if rank:
            return {
                "name": name,
                "isGhost": False,
                "rank": rank,
                "totalScore": totalScore
            }
        else:
            return None

    self._getNemesis = _getNemesis

    def _getRank():
        nem = self._getNemesis()
        if nem:
            return nem["rank"] + 1
        else:
            return 1

    self._getRank = _getRank

    async def _getProgress(q=None):
        if q is None:
            return this._httpRequest(f"https://kahoot.it/rest/challenges/{self.challengeData["challenge"]["challengeId"]}/progress/?upToQuestion={q}",None,True)
        else:
            data = await this._httpRequest(f"https://kahoot.it/rest/challenges/pin/{this.gameid}",None,True)
            data2 = await this._httpRequest(f"https://kahoot.it/rest/challenges/{data.challenge.challengeId}/progress",None,True)
            data.update(data2)
            return data

    self._getProgress = _getProgress

    inf = self._getProgress()
    if len(inf["progress"]) == 0:
        self.disconnectReason = "Invalid Challenge"
        try:
            self.socket.close()
        except Exception:
            pass
        return
    self.challengeData = inf
    if inf["challenge"]["endTime"] <= time.time() * 1000 or len(inf["challenge"]["challengeUsersList"]) >= inf["challenge"]["maxPlayers"]:
        self.disconnectReason = "Challenge Ended/Full"
        try:
            self.socket.close()
        except Exception:
            pass
        return
    else:
        self.emit("HandshakeComplete")

class ChallengeHandler(EventEmitter):
    __init__(self,client,content):
        super().__init__()
        client.challengeData = content
        Injector(client)
        self.readyState = 3
        def close():
            self.stop = True
            try:
                client.ti.cancel()
            except Exception:
                raise
            self.on_close()
        self.close = close
