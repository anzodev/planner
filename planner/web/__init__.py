import flask

from planner.web import api
from planner.web import database
from planner.web.config import Config


def create_app(config: Config) -> flask.Flask:
    app = flask.Flask(__name__)
    app.config.from_object(config)

    database.init_app(app)
    api.init_app(app)

    return app
