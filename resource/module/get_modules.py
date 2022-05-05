from flask_apispec import MethodResource
from flask_apispec import doc
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import json

from db.db import DB
from decorator.catch_exception import catch_exception
from decorator.verify_admin_access import verify_admin_access


class GetModules(MethodResource, Resource):

    def __init__(self, db: DB):
        self.db = db

    @doc(tags=['module'])
    # @jwt_required
    # @verify_admin_access
    @catch_exception
    def get(self):

        f = open("config/cron_config.json", "r")
        cron_config = f.read()
        cron_config = json.loads(cron_config)

        return cron_config
