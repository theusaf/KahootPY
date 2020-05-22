from . import consts
import requests
import urllib
import time
import math
from user_agent import generate_user_agent as UserAgent
import re
import base64
# GET the token
def requestToken(sessionID,callback,proxy):
    proxyOptions = None
    nopath = None
    if type(proxy) == type(str()):
        proxy = proxy or ""
    elif proxy and proxy.get("proxy"):
        proxyOptions = proxy.get("options") or {}
        nopath = proxy.get("nopath")
        proxy = proxy.get("proxy")
    else:
        proxy = ""
    uri = None
    if not nopath:
        if proxy and proxy[-1] == "/":
            uri = proxy + "https://" + consts.ENDPOINT_URI + consts.TOKEN_ENDPOINT + str(sessionID) + "/?" + str(math.floor(time.time() * 1000))
        elif proxy:
            uri = proxy + "/https://" + consts.ENDPOINT_URI + consts.TOKEN_ENDPOINT + str(sessionID) + "/?" + str(math.floor(time.time() * 1000))
        else:
            uri = "https://" + consts.ENDPOINT_URI + consts.TOKEN_ENDPOINT + str(sessionID) + "/?" + str(math.floor(time.time() * 1000))
    _uri = urllib.parse.urlparse(uri)
    options = {
        "port": consts.ENDPOINT_PORT,
        "headers": {
            "user-agent": UserAgent(),
            "host": (proxy and uri.hostname) or "kahoot.it",
            "referer": "https://kahoot.it/",
            "accept-language": "en-US,en;q=0.8",
            "accept": "*/*"
        }
    }
    if proxyOptions:
        options.update(proxyOptions)
    r = requests.get(uri);
    if not r.headers.get("x-kahoot-session-token"):
        return callback(None,None,None)
    try:
        data = r.json()
    except Exception as e:
        return callback(None,e,None)
    callback(r.headers.get("x-kahoot-session-token"),data["challenge"],data)
# Evaluate the JS challenge
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
    return token;
# main function
def resolve(sessionID,callback,proxy=None):
    if str(sessionID)[0] == "0":
        return requestChallenge(sessionID,callback,proxy)
    def _(headerToken,challenge,gamemode):
        if not headerToken:
            return callback(None,None)
        token1 = decodeBase64(headerToken)
        token2 = solveChallenge(challenge)
        resolvedToken = concatTokens(token1,token2)
        callback(resolvedToken,gamemode)
    requestToken(sessionID,_,proxy)
# getting challenge stuff
def requestChallenge(sessionID,callback,proxy):
    proxyOptions = None
    nopath = None
    if type(proxy) == type(str()):
        proxy = proxy or ""
    elif proxy and proxy.get("proxy"):
        proxyOptions = proxy.get("options") or {}
        nopath = proxy.get("nopath")
        proxy = proxy.get("proxy")
    else:
        proxy = ""
    uri = None
    if not nopath:
        if proxy[-1] == "/":
            uri = proxy + "https://" + consts.ENDPOINT_URI + consts.CHALLENGE_ENDPOINT + "/pin/" + sessionID
        else:
            uri = proxy + "/https://" + consts.ENDPOINT_URI + consts.CHALLENGE_ENDPOINT + "/pin/" + sessionID
    _uri = urllib.parse.urlparse(uri)
    options = {
        "port": consts.ENDPOINT_PORT,
        "headers": {
            "user-agent": UserAgent(),
            "host": (proxy and uri.hostname) or "kahoot.it",
            "referer": "https://kahoot.it/",
            "accept-language": "en-US,en;q=0.8",
            "accept": "*/*"
        }
    }
    if proxyOptions:
        options.update(proxyOptions)
    r = requests.get(uri);
    try:
        data = r.json()
    except Exception as e:
        return callback(None,e,None)
    try:
        inf = {
            "twoFactorAuth": False,
            "gameMode": data["challenge"]["type"],
            "kahootData": data["kahoot"],
            "rawChallengeData": data["challenge"]
        }.update(data["challenge"]["game_options"])
        return callback(True,inf)
    except Exception as e:
        return callback(None,e,None)
