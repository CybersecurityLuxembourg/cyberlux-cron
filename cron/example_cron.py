
class ExampleCron:

    def __init__(self, db):
        self.db = db

    def run(self):
        print(self.db)
        print("Happy!")
