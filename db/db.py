from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy


class SA(SQLAlchemy):
    def apply_pool_defaults(self, app, options):
        SQLAlchemy.apply_pool_defaults(self, app, options)
        options["pool_pre_ping"] = True
        options["pool_recycle"] = 60


class DB:
    def __init__(self, app):

        # Init instance

        self.instance = SA(app)
        self.instance.init_app(app)

        self.base = None
        self.session = self.instance.session
        self.engine = self.instance.engine

        # Init the table objects

        self.tables = {}
        self.base = declarative_base()
        self.base.metadata = MetaData(bind=self.instance)

        for table in self.engine.table_names():
            attr = {'__tablename__': table, '__table_args__': {'autoload': True, 'autoload_with': self.engine}}
            self.tables[table] = type(table, (self.base,), attr)

    ###############
    # GLOBAL      #
    ###############

    def merge(self, data, table, commit=True):
        if isinstance(data, dict):
            data = table(**data)
            data = self.session.merge(data)
        elif isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    row = table(**row)
                self.session.merge(row)
        else:
            data = self.session.merge(data)

        if commit:
            self.session.commit()

        return data

    def insert(self, data, table, commit=True):
        if isinstance(data, dict):
            data = table(**data)
            self.session.add(data)
        else:
            for row in data:
                if isinstance(row, dict):
                    row = table(**row)
                self.session.add(row)

        if commit:
            self.session.commit()

        return data

    def delete(self, table, filters=None, commit=True):
        if filters is not None:
            q = self.session.query(table)
            for attr, value in filters.items():
                if isinstance(value, list):
                    q = q.filter(getattr(table, attr).in_(value))
                else:
                    q = q.filter(getattr(table, attr) == value)
            q.delete()

            if commit:
                self.session.commit()

    def delete_by_id(self, id_, table):
        self.session.query(table).filter(table.id == id_).delete()
        self.session.commit()

    def truncate(self, table):
        self.session.query(table).delete()
        self.session.commit()

    def get(self, table, filters=None, entities=None):
        filters = {} if filters is None else filters
        q = self.session.query(table)

        if entities is not None:
            q = q.with_entities(*entities)

        for attr, value in filters.items():
            if isinstance(value, list):
                q = q.filter(getattr(table, attr).in_(value))
            elif isinstance(value, bool):
                q = q.filter(getattr(table, attr).is_(value))
            else:
                q = q.filter(getattr(table, attr) == value)

        return q.all()

    def get_count(self, table, filters=None):
        filters = {} if filters is None else filters
        q = self.session.query(table)
        for attr, value in filters.items():
            if isinstance(value, list):
                q = q.filter(getattr(table, attr).in_(value))
            else:
                q = q.filter(getattr(table, attr) == value)
        return q.count()

    def get_by_id(self, id_, table):
        return self.session.query(table).filter(table.id == id_).one()

    ###############
    # UTILS       #
    ###############

    @staticmethod
    def are_objects_equal(a, b, table):
        for c in table.__table__.columns.keys():
            if getattr(a, c) != getattr(b, c):
                return False
        return True
