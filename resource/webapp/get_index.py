from flask_restful import Resource
from flask import make_response, render_template
from resource.healthz import Healthz
from resource.engine.get_thread_count import GetThreadCount
from resource.engine.get_worker_count import GetWorkerCount
from db.db import DB


class GetIndex(Resource):

    def __init__(self, db: DB, engine):
        self.db = db
        self.engine = engine

    def get(self):
        response = make_response(render_template(
            'index.html',
            status=Healthz(self.db).get().status,
            thread_count=GetThreadCount(self.engine).get().data.decode("utf-8"),
            worker_count=GetWorkerCount(self.engine).get().data.decode("utf-8"),
        ))
        response.headers['Content-Type'] = 'text/html; charset=ISO-8859-1'

        return response
