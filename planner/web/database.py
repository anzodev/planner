import peewee as pw
from flask import Flask
from flask import current_app
from flask import g

from planner.core.models import Task
from planner.core.models import User
from planner.core.models import db as models_db


def init_app(app: Flask) -> None:
    db = pw.SqliteDatabase(
        app.config["DB_PATH"],
        pragmas=[
            ("cache_size", -1024 * 64),
            ("journal_mode", "wal"),
            ("foreign_keys", 1),
        ],
    )
    models_list = [User, Task]

    with db.bind_ctx(models_list):
        db.create_tables(models_list)

    app.config["DATABASE"] = db

    @app.before_request
    def enable_database():
        g._origin_db = models_db.obj
        models_db.initialize(current_app.config["DATABASE"])

    @app.teardown_request
    def disable_database(*_):
        models_db.initialize(g._origin_db)
