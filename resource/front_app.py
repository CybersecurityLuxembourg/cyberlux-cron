from flask_restful import Resource
from flask import make_response, render_template
from resource.healthz import Healthz
from resource.engine.get_thread_count import GetThreadCount
from resource.engine.get_worker_count import GetWorkerCount
from db.db import DB


class FrontApp(Resource):

    def __init__(self, db: DB, engine):
        self.db = db
        self.engine = engine

    def get(self):

        response = make_response(render_template(
            'index.html',
            status=Healthz(self.db).get().status,
            thread_count=GetThreadCount(self.engine).get().status,
            worker_count=GetWorkerCount(self.engine).get().status,
        ))
        response.headers['Content-Type'] = 'text/html; charset=ISO-8859-1'

        return response
