from kahoot import client
pin = 3076110
bot = client()
bot.loggingMode = True
bot.join(pin,"foobar")
def joined():
    print("joined")
bot.on("ready",joined)
def badname():
    print("leaving")
    bot.leave()
bot.on("invalidName",badname)
def answer():
    bot.answer(0)
bot.on("questionStart",answer)
def qs():
    print("question started")
    pass
bot.on("quizStart",qs)
