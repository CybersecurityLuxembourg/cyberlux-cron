from flask_apispec import MethodResource
from flask_apispec import use_kwargs, doc
from flask_restful import Resource
from webargs import fields, validate

from db.db import DB
from decorator.catch_exception import catch_exception
from utils.serializer import Serializer


class GetCronLog(MethodResource, Resource):

    def __init__(self, db: DB):
        self.db = db

    @doc(tags=['log'],
         description='Get logs of the cron tasks',
         responses={
             "200": {},
         })
    @use_kwargs({
        'page': fields.Int(required=False, missing=1, validate=validate.Range(min=1)),
        'per_page': fields.Int(required=False, missing=50, validate=validate.Range(min=1, max=50)),
        'order': fields.Str(required=False, missing='desc', validate=lambda x: x in ['desc', 'asc']),
    }, location="query")
    @catch_exception
    def get(self, **kwargs):

        query = self.db.session.query(self.db.tables["Log"]) \
            .filter(self.db.tables["Log"].request.like(f"%cron%"))

        if "order" in kwargs and kwargs["order"] == "desc":
            query = query.order_by(self.db.tables["Log"].sys_date.desc())
        else:
            query = query.order_by(self.db.tables["Log"].sys_date.asc())

        pagination = query.paginate(kwargs["page"], kwargs["per_page"])
        logs = Serializer.serialize(pagination.items, self.db.tables["Log"])

        return {
            "pagination": {
                "page": kwargs["page"],
                "pages": pagination.pages,
                "per_page": kwargs["per_page"],
                "total": pagination.total,
            },
            "items": logs,
        }, "200 "
