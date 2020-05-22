class Quiz():
    def __init__(self, name, type, answerCount, client, amount, answers, rawData):
        self.client = client
        self.name = name
        self.type = type
        self.answerCount = answerCount
        self.currentQuestion = None
        self.questions = []
        self.questionCount = amount
        self.answerCounts = answers
        self.rawEvent = rawData

class Question():
    def __init__(self,rawEvent,client):
        self.client = client
        self.quiz = client.quiz
        self.index = rawEvent["questionIndex"]
        self.timeLeft = rawEvent["timeLeft"]
        self.type = rawEvent["type"]
        self.usesStoryBlocks = rawEvent.get("useStoryBlocks")
        self.ended = False
        self.quiz.questions.append(self)
        self.number = len(self.quiz.questions)
        self.quiz.currentQuestion = self
        self.rawEvent = rawEvent
    def answer(self,number,secret={}):
        if not number and number != 0:
            return False
        self.client.answerQuestion(number,self,secret)

class QuestionEndEvent():
    def __init__(self,rawEvent,client):
        try:
            self.client = client
            self.quiz = client.quiz
            self.question = self.quiz.questions[-1]
            self.question.ended = True
            self.correctAnswers = rawEvent.get("correctAnswers")
            self.correctAnswer = self.correctAnswers[0]
            self.text = rawEvent.get("text")
            self.correct = rawEvent["correct"]
            self.nemesis = Nemesis(rawEvent.get("nemesis"))
            self.points = rawEvent["points"]
            self.rank = rawEvent["rank"]
            self.total = rawEvent["totalScore"]
            self.streak = rawEvent["pointsData"]["answerStreakPoints"]["streakLevel"]
            self.rawEvent = rawEvent
        except Exception as e:
            return e

class QuestionSubmitEvent():
    def __init__(self,message,client):
        self.client = client
        self.quiz = client.quiz
        self.question = self.quiz.questions[-1]
        self.rawEvent = message

class Nemesis():
    def __init__(self,rawData):
        if rawData:
            self.name = rawData.get("name")
            self.score = rawData.get("totalScore")
            self.isGhost = rawData.get("isGhost")
            self.exists = True
            self.rawEvent = rawData
        else:
            self.name = None
            self.score = None
            self.isKicked = None
            self.exists = False
            self.rawEvent = None

class FinishTextEvent():
    def __init__(self,rawEvent):
        self.metal = rawEvent["metal"]
        self.rawEvent = rawEvent

class QuizFinishEvent():
    def __init__(self,rawEvent,client):
        self.client = client
        self.quiz = client.quiz
        self.players = rawEvent["playerCount"]
        self.quizID = rawEvent["quizID"]
        self.rank = rawEvent["rank"]
        self.correct = rawEvent["correct"]
        self.incorrect = rawEvent["incorrect"]
        self.rawEvent = rawEvent
