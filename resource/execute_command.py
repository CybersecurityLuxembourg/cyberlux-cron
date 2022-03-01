from flask_restful import Resource
from queue import Queue


class ExecuteCommand(Resource):

    def __init__(self, engine):
        self.engine = engine

    def get(self, command):
        try:
            message_queue = Queue(1)
            self.engine.queue.put((message_queue, command))
            res = message_queue.get(timeout=1)
            del message_queue
        except Exception as e:
            raise e
        return res, 200
