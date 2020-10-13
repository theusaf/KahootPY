from .LiveTimesyncData import LiveTimesyncData

class LiveClientHandshake():
    def __init__(self,n,m,c):
        if str(s) == "2":
            self["channel"] = "/meta/connect"
            self["ext"] = {
                "ack": m["ext"]["ack"]
            }
            self["clientId"] = c["clientId"]
        elif str(s) == "1":
            self["advice"] = {
                "timeout": 0
            }
            self["channel"] = "/meta/connect"
            self["ext"] = {
                "ack": 0,
                "timesync": LiveTimesyncData(n,m["l"],m["o"])
            }
            self["clientId"] = c["clientId"]
        else:
            self["advice"] = {
                "interval": 0,
                "timeout": 60000
            }
            self["minimumVersion"] = "1.0"
            self["version"] = "1.0"
            self["supportedConnectionTypes"] = [
                "websocket",
                "long-polling"
            ]
            self["channel"] = "/meta/handshake"
            self["ext"] = LiveTimesyncData(n)
