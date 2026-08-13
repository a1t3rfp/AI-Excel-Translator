import threading


class TranslationWorker(threading.Thread):

    def __init__(self, func):
        super().__init__()

        self.func = func

        self.daemon = True

    def run(self):

        self.func()