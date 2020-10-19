def main(self):
    self.data["totalScore"] = 0
    self.data["streak"] = 0
    self.data["rank"] = 1
    def GameResetHandler():
        self.data["totalScore"] = 0
        self.data["rank"] = 0
        self.data["streak"] = 0
        self.quiz = None
    self.on("GameReset",GameResetHandler)
    def QuestionStartHandler(event):
        def typ(self):
            return self["type"]
        def index(self):
            return self["questionIndex"]
        event.update({
            "answer": self.answer,
            "type": property(typ),
            "index": property(index)
        })
    self.on("QuestionStart",QuestionStartHandler)
    def QuizStartHandler(event):
        def questionCount(self):
            return len(self.quizQuestionAnswers)
        event.update({
            "questionCount": property(questionCount)
        })
        try:
            self.quiz.update(event)
        except Exception:
            pass
    self.on("QuizStart",QuizStartHandler)
    def QuestionReadyHandler(event):
        def typ(self):
            return self["gameBlockType"]
        def index(self):
            return self["questionIndex"]
        event.update({
            "type": property(typ),
            "index": property(index)
        })
        try:
            self.quiz["currentQuestion"].update(event)
        except Exception:
            pass
    self.on("QuestionReady",QuestionReadyHandler)
    def QuestionEndHandler(event):
        self.data["totalScore"] = event["totalScore"]
        self.data["streak"] = event["pointsData"]["answerStreakPoints"]["streakLevel"]
        self.data["rank"] = event["rank"]
    self.on("QuestionEnd",QuestionEndHandler)
