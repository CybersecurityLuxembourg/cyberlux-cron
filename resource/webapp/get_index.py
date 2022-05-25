from flask_restful import Resource
from flask import make_response, render_template
from resource.healthz import Healthz
from db.db import DB


class GetIndex(Resource):

    def __init__(self, db: DB, engine):
        self.db = db
        self.engine = engine

    def get(self):
        response = make_response(render_template(
            'index.html',
            status=Healthz(self.db).get().status,
        ))
        response.headers['Content-Type'] = 'text/html; charset=ISO-8859-1'

        return response
