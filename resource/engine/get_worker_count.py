from flask_apispec import MethodResource
from flask_apispec import doc
from flask import make_response, jsonify
from flask_restful import Resource
from queue import Queue


class GetWorkerCount(MethodResource, Resource):

    def __init__(self, engine):
        self.engine = engine

    @doc(tags=['engine'],
         responses={
            "200": {},
         })
    def get(self):
        try:
            message_queue = Queue(1)
            self.engine.queue.put((message_queue, "GET_NUMBER_OF_WORKERS"))
            res = message_queue.get(timeout=1)
            del message_queue
        except Exception as e:
            raise e

        response = make_response(jsonify(res), 200)
        response.headers['Content-Type'] = 'text/plain; charset=ISO-8859-1'

        return response, 200
