class ClientError(Exception):
    def __init__(self, desc):
        super().__init__(desc)
        self.desc = desc

class SubprocessError(ClientError):
    def __init__(self, desc):
        super().__init__(desc)
        self.desc = desc
        self.output = None

class DeployError(ClientError):
    def __init__(self, desc):
        super().__init__(desc)
        self.desc = desc
