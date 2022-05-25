import functools

from flask_jwt_extended import get_jwt_identity


def verify_admin_access(function):
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):

        # Checking the user

        users = getattr(self, "db").get(
            getattr(self, "db").tables["User"],
            {"id": int(get_jwt_identity()) if get_jwt_identity() is not None else None})

        if len(users) == 0:
            return "", "401 The user has not been found"

        if users[0].is_admin == 0:
            return "", "401 This user is not an admin"

        return function(self, *args, **kwargs)

    return wrapper
