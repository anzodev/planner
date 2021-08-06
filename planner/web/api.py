import logging

from flask import Blueprint
from flask import Flask
from flask import Response
from flask import redirect
from flask import render_template
from flask import url_for
from werkzeug.exceptions import HTTPException

from planner.web import auth


def init_app(app: Flask) -> None:
    pages_bp = Blueprint("pages", __name__)
    forms_bp = Blueprint("forms", __name__, url_prefix="/forms")

    # fmt: off
    page = lambda url, ep: pages_bp.route(url, endpoint=ep, methods=["GET"])  # noqa: E731, E501
    form = lambda url, ep: forms_bp.route(url, endpoint=ep, methods=["POST"])  # noqa: E731, E501
    # fmt: on

    @page("/login", "login")
    def _():
        return render_template("pages/login.html")

    @page("/registration", "registration")
    def _():
        return render_template("pages/registration.html")

    @page("/", "index")
    @auth.has_access
    def _():
        return render_template("pages/active-tasks.html")

    @page("/tasks/<int:task_id>", "task")
    @auth.has_access
    def _(task_id: int):
        return render_template("pages/task.html")

    @form("/create-user", "create_user")
    @auth.has_access
    def _():
        ...

    @form("/login", "login")
    @auth.has_access
    def _():
        ...

    @form("/logout", "logout")
    @auth.has_access
    def _():
        ...

    # @form("/tasks/create")
    # @auth.has_access
    # def _():
    #     ...

    # @form("/tasks/remove")
    # @auth.has_access
    # def _():
    #     ...

    # @form("/tasks/complete")
    # @auth.has_access
    # def _():
    #     ...

    @app.errorhandler(Exception)
    def errorhandler(exc: Exception) -> Response:
        if isinstance(exc, auth.NotAuthorized):
            return redirect(url_for("pages.login"))

        status_code = 500
        description = (
            "Sorry, something goes wrong."
            " Try to repeat your request a few minutes later."
        )

        if isinstance(exc, HTTPException):
            status_code = exc.code
            description = exc.description

        if status_code == 500:
            logger = logging.getLogger(__name__)
            logger.exception("unexpected error:")

        return render_template(
            "pages/error.html", status_code=status_code, description=description
        )

    app.register_blueprint(pages_bp)
    app.register_blueprint(forms_bp)
