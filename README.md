# About
KahootPY is a library to interact with the Kahoot API. KahootPY supports joining and interacting with quizzes and challenges.

# Installation

`pip install -U KahootPY`

# Usage

```py
from kahoot import client
bot = client()
bot.join(12345,"KahootPY")
def joinHandle():
  pass
bot.on("Joined",joinHandle)
```

# Documentation:
See [kahoot.js-updated](https://github.com/theusaf/kahoot.js-updated/blob/master/Documentation.md). The API is very similar with some differences listed below:

Instead of `Promise`s, KahootPY methods return `Futures`

Proxying works similarly, but only accepts finished requests or request options.

Finished requests must have a `headers` object and a `text` property
