import time

class LiveTimesyncData(dict):
    def __init__(self,n,l,o):
        super().__init__()
        if str(n) == "1":
            self.timesync = {
                "l": l,
                "o": o,
                "tc": int(time.time() * 1000)
            }
        else:
            self.ack = True,
            self.timesync = {
                "l": 0,
                "o": 0,
                "tc": int(time.time() * 1000)
            }
