from functools import wraps

from flask import g
from flask import session

from planner.core.models import User


class NotAuthorized(Exception):
    ...


def authorize_user(user: User) -> None:
    session["uid"] = user.id
    session["uname"] = user.username


def forget_user() -> None:
    session.pop("uid", None)
    session.pop("uname", None)


def is_user_in_session() -> bool:
    return "uid" in session


def has_access(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "uid" not in session or "uname" not in session:
            raise NotAuthorized()

        g.user_id = session["uid"]
        g.user_username = session["uname"]

        return f(*args, **kwargs)

    return wrapper
