class LiveBaseMessage(dict):
    def __init__(self,client,channel,data=None):
        super().__init__()
        self["channel"] = channel
        self["clientId"] = client.clientId
        if data:
            self["data"] = data
            self["ext"] = {}
