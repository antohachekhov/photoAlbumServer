class Session:
    directoryStart = ''

    def __init__(self, user=None):
        self.directoryCurrent = Session.directoryStart
        self.user = user
