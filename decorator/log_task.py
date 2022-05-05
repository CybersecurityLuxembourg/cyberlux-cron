import functools
from flask import Response


def log_task(function):
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        a = function(self, *args, **kwargs)

        log = {
            "user_id": None,
            "request": '/{}.{}'.format(function.__module__, function.__qualname__)
                       .replace(".", "/"),
            "request_method": "CRON",
            "params": None,
            "status_code": a.status_code if isinstance(a, Response) else int(str(a[1][0:3])),
            "status_description": a.status if isinstance(a, Response) else a[1][4:][:150]
        }

        getattr(self, "db").insert(log, getattr(self, "db").tables["Log"])

        return a

    return wrapper
