# About
KahootPY is a library to interact with the Kahoot API. KahootPY supports joining and interacting with quizzes and ~challenges (not yet)~.

# Installation

`pip install -U KahootPY`

```py
from kahoot import client
bot = client()
bot.join(12345,"KahootPY")
def joinHandle():
  pass
bot.on("joined",joinHandle)
```

Since this is basically a translation of JavaScript to Python, expect issues and bugs.

Documentation:
See [kahoot.js-updated](https://github.com/theusaf/kahoot.js-updated/blob/master/Documentation.md). The API is very similar, besides having no Promises.
