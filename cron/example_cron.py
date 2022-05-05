from decorator.log_task import log_task
from flask import Response


class ExampleCron:

    def __init__(self, db):
        self.db = db

    @log_task
    def run(self):
        print("Happy!")
        print(self.db)

        return Response(status="200 Coucou")
