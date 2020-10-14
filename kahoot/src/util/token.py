import urllib
import time
import re
import base64
import math
import requests
import urllib
import time
import asyncio
import json as JSON
from user_agent import generate_user_agent as UserAgent

loop = asyncio.get_event_loop()

async def requestChallenge(pin,client):
    options = {
        "headers": {
            "User-Agent": UserAgent(),
            "Origin": "kahoot.it",
            "Referer": "https://kahoot.it",
            "Accept-Language": "en-US,en;q=0.8",
            "Accept": "*/*"
        },
        "host": "kahoot.it",
        "protocol": "https:",
        "path": f"/rest/challenges/pin/{pin}"
    }
    proxyOptions = await client.defaults["proxy"](options)
    # proxy options either returns the options listed above
    # or returns an object with:
    # - headers (list of headers)
    # - text (text response)
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
        url = (options.get("protocol") or "https:") + "//" + (options.get("host") or "kahoot.it") + (options.get("port") or "") + options.get("path")
        r = requests.request(options.get("method") or "GET",url,headers=options.get("headers"))
    try:
        data = r.json()
        out = {
            "data": {
                "isChallenge": True,
                "twoFactorAuth": False,
                "kahootData": data.get("kahoot"),
                "rawChallengeData": data["challenge"]
            }
        }
        out["data"].update(data["challenge"]["game_options"])
        return out
    except Exception as e:
        raise e

async def requestToken(pin,client):
    options = {
        "headers": {
            "User-Agent": UserAgent(),
            "Origin": "kahoot.it",
            "Referer": "https://kahoot.it",
            "Accept-Language": "en-US,en;q=0.8",
            "Accept": "*/*"
        },
        "host": "kahoot.it",
        "protocol": "https:",
        "path": f"/reserve/session/{pin}/?{int(time.time() * 1000)}"
    }
    proxyOptions = await client.defaults["proxy"](options)
    # proxy options either returns the options listed above
    # or returns an object with:
    # - headers (list of headers)
    # - text (text response)
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
        url = (options.get("protocol") or "https:") + "//" + (options.get("host") or "kahoot.it") + (options.get("port") or "") + options.get("path")
        r = requests.request(options.get("method") or "GET",url,headers=options.get("headers"))
    if not r.headers.get("x-kahoot-session-token"):
        raise "Invalid PIN"
    try:
        data = r.json()
        token = r.headers.get("x-kahoot-session-token")
        return {
            "token": token,
            "data": data
        }
    except Exception as e:
        raise e

def solveChallenge(challenge):
    solved = ""
    anti_whitespace = re.compile(r'(\u0009|\u2003)',re.M)
    challenge = anti_whitespace.sub("",challenge)
    challenge = re.sub("this ","this",challenge)
    anti_dot = re.compile(r' *\. *',re.M)
    challenge = anti_dot.sub(".",challenge);
    anti_paren1 = re.compile(r' *\( *',re.M)
    anti_paren2 = re.compile(r' *\) *',re.M)
    challenge = anti_paren1.sub("(",challenge)
    challenge = anti_paren2.sub(")",challenge)
    challenge = re.sub("console.","",challenge);
    challenge = re.sub("this\.angular\.isObject\(offset\)", "true",challenge);
    challenge = re.sub("this\.angular\.isString\(offset\)", "true",challenge);
    challenge = re.sub("this\.angular\.isDate\(offset\)", "true",challenge);
    challenge = re.sub("this\.angular\.isArray\(offset\)", "true",challenge);
    challenge = _challengeToPython(challenge)
    edict={}
    exec(challenge,globals(),edict)
    return edict["fin"]
# Convert the JS to Python
def _challengeToPython(challenge):
    challenge = re.sub(r"\.call\(this,","(",challenge)
    challenge = re.sub(r";\s*","\n",challenge)
    challenge = re.compile('function',re.M).sub("def",challenge)
    challenge = re.compile(r'\)\{',re.M).sub("):\n\t",challenge)
    challenge = re.sub("true","True",challenge)
    challenge = re.compile(r"char\.charCodeAt\(0\)").sub("ord(char)",challenge)
    challenge = re.compile(r"String\.fromCharCode").sub("chr",challenge)
    challenge = re.sub(r"var\s+offset","offset",challenge)
    challenge = re.compile(r"if\(True\)").sub("\tif(True):\n\t\t",challenge)
    challenge = re.compile("return",re.M).sub("\treturn",challenge)
    challenge = re.compile(r"\s+def\(char",re.M).sub("\n\tdef repl(char",challenge)
    challenge = re.compile(r"return\s+_",re.M).sub("#",challenge)
    challenge = re.compile(r"message\):",re.M).sub("message):\n\tdef log(a,b,c):\n\t\tpass\n",challenge)
    # challenge = "def log(a,b,c):\n\tpass\n" + challenge
    call = re.search(r"decode\(.*\)$",challenge,re.M).group(0)
    challenge = re.compile(r"decode\(.*\)$",re.M).sub("",challenge)
    challenge = re.compile(r"^\}\)?",re.M).sub("",challenge)
    challenge = re.compile(r"\)\n\n",re.M).sub(")\n\tres=\"\"\n\tfor i in range(0,len(message)):\n\t\tres+=repl(message[i],i)\n\treturn res",challenge)
    challenge += "\nfin=" + call
    return challenge
# Decode the token header
def decodeBase64(base):
    try:
        base += "=" * ((4 - len(base) % 4) % 4)
        return base64.b64decode(base).decode("utf-8")
    except Exception as e:
        return e
# complex stuff to get the actual token
def concatTokens(headerToken,challengeToken):
    token = ""
    for i in range(0,len(headerToken)):
        char = ord(headerToken[i])
        mod = ord(challengeToken[i % len(challengeToken)])
        decodedChar = char ^ mod
        token += chr(decodedChar)
    return token

async def resolve(pin,client):
    if math.isnan(pin):
        raise "Missing PIN"
    if str(pin[0]) == "0":
        return requestChallenge(pin,client)
    data = await requestToken(pin,client)
    token2 = solveChallenge(data["data"]["challenge"])
    token = concatTokens(data["token"],token2)
    return {
        "token": token,
        "data": data["data"]
    }
