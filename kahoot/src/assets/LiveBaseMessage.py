class LiveBaseMessage():
    def __init__(self,client,channel,data):
        self.channel = channel
        self.clientId = client["clientId"]
        if data:
            self.data = data
            self.ext = {}
