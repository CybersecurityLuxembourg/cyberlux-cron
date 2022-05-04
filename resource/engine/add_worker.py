from flask_apispec import MethodResource
from flask_apispec import doc
from flask_restful import Resource
from queue import Queue


class AddWorker(MethodResource, Resource):

    def __init__(self, engine):
        self.engine = engine

    @doc(tags=['engine'])
    def post(self):
        try:
            message_queue = Queue(1)
            self.engine.queue.put((message_queue, "ADD_WORKER"))
            res = message_queue.get(timeout=1)
            del message_queue
        except Exception as e:
            del message_queue
            return str(e), 200

        return res, 200
