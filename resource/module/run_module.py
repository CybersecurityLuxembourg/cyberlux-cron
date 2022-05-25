from flask_apispec import MethodResource
from flask_apispec import use_kwargs, doc
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import sys
import importlib
from webargs import fields

from db.db import DB
from decorator.catch_exception import catch_exception
from decorator.verify_admin_access import verify_admin_access


class RunModule(MethodResource, Resource):

    def __init__(self, db: DB, engine):
        self.db = db
        self.engine = engine

    @doc(tags=['module'])
    @use_kwargs({
        'module': fields.Str(required=True),
    })
    @jwt_required
    @verify_admin_access
    @catch_exception
    def post(self, **kwargs):

        # Check if the module arg has the right format

        if not kwargs["module"].startswith("cron.") \
                or len(kwargs["module"].split(".")) != 3:
            return "", "422 The module should have this format 'cron.XXX.XXX'"

        # Check if the module is available

        try:
            class_name = kwargs["module"].split(".")[-1]
            package_name = (".".join(kwargs["module"].split(".")[0:-1]))
            if package_name not in sys.modules:
                package = importlib.import_module(package_name)
            else:
                package = importlib.reload(importlib.import_module(package_name))
            module_class = getattr(package, class_name)
        except Exception:
            return "", "422 The specified module has not been found"

        config = {
            "class": module_class,
            "config": {},
        }

        # Run module

        self.engine.cron_queue.execute_cron(config)

        return "", "200 "
