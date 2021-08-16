import logging

from flask import Blueprint
from flask import Flask
from flask import Response
from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import HTTPException

from planner.core.models import Task
from planner.core.models import User
from planner.core.usecase import tasks as task_usecase
from planner.core.usecase import users as user_usecase
from planner.web import app_runtime_helpers
from planner.web import auth
from planner.web import notify


def init_app(app: Flask) -> None:
    pages_bp = Blueprint("pages", __name__)
    forms_bp = Blueprint("forms", __name__, url_prefix="/forms")

    # fmt: off
    page = lambda url, ep: pages_bp.route(url, endpoint=ep, methods=["GET"])  # noqa: E731, E501
    form = lambda url, ep: forms_bp.route(url, endpoint=ep, methods=["POST"])  # noqa: E731, E501
    # fmt: on

    @page("/login", "login")
    def _():
        if auth.is_user_in_session():
            return redirect(url_for("pages.index"))
        return render_template("pages/login.html")

    @page("/sign-up", "sign_up")
    def _():
        return render_template("pages/sign-up.html")

    @page("/", "index")
    @auth.has_access
    def _():
        return redirect(url_for("pages.active_tasks"))

    @page("/active-tasks", "active_tasks")
    @auth.has_access
    def _():
        # fmt: off
        active_tasks = (
            Task
            .select()
            .where(
                (Task.progress != 100)
                & (Task.parent_task.is_null())
                & (Task.user_id == g.user_id)
            )
            .order_by(Task.created_at.desc())
        )
        # fmt: on
        return render_template("pages/active-tasks.html", tasks=active_tasks)

    @page("/completed-tasks", "completed_tasks")
    @auth.has_access
    def _():
        args = request.args
        offset = int(args.get("offset", "0"))
        limit = int(args.get("limit", current_app.config["COMPLETED_TASKS_LIMIT"]))

        # fmt: off
        completed_tasks_plus_one = list(
            Task
            .select()
            .where(
                (Task.progress == 100)
                & (Task.parent_task.is_null())
                & (Task.user_id == g.user_id)
            )
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit + 1)
        )
        # fmt: on
        completed_tasks = completed_tasks_plus_one[:limit]

        has_next = len(completed_tasks_plus_one) > limit
        has_previous = offset > 0

        return render_template(
            "pages/completed-tasks.html",
            tasks=completed_tasks,
            has_next=has_next,
            has_previous=has_previous,
            offset=offset,
            limit=limit,
        )

    @page("/tasks/<int:task_id>", "task")
    @auth.has_access
    def _(task_id: int):
        task = Task.get_or_none(id=task_id, user_id=g.user_id)
        if task is None:
            abort(404)

        # fmt: off
        subtasks = (
            Task
            .select()
            .where(
                Task.parent_task == task
            )
        )
        # fmt: on

        return render_template(
            "pages/task.html",
            task=task,
            parent_task=task.parent_task,
            subtasks=subtasks,
        )

    @form("/sign-up", "sign_up")
    def _():
        form = request.form
        username = form["username"]
        password = form["password"]
        password_copy = form["password_copy"]

        if password != password_copy:
            notify.error("Passwords missmatch!")
            return redirect(url_for("pages.sign_up"))

        if User.select(User.username).where(User.username == username).exists():
            notify.error(f"User '{username}' exists already.")
            return redirect(url_for("pages.sign_up"))

        password_hasher = app_runtime_helpers.init_password_hasher()
        user_usecase.create_user(username, password_hasher, password)

        return redirect(url_for("pages.login"))

    @form("/login", "login")
    def _():
        form = request.form
        username = form["username"]
        password = form["password"]

        user = User.get_or_none(username=username)
        if user is None:
            notify.error("Username/password is invalid.")
            return redirect(url_for("pages.login"))

        password_hasher = app_runtime_helpers.init_password_hasher()
        if not password_hasher.is_hash_correct(user.password_hash, password):
            notify.error("Username/password is invalid.")
            return redirect(url_for("pages.login"))

        auth.authorize_user(user)

        return redirect(url_for("pages.index"))

    @form("/logout", "logout")
    @auth.has_access
    def _():
        auth.forget_user()
        return redirect(url_for("pages.login"))

    @form("/tasks/create", "create_task")
    @auth.has_access
    def _():
        form = request.form
        name = form["name"]
        extra_info = form.get("extra_info")
        parent_task_id = form.get("parent_task_id")

        user = User.get_by_id(g.user_id)
        parent_task = None
        if parent_task_id is not None:
            parent_task = Task.get_or_none(id=parent_task_id, user=user)

        task_usecase.create_task(
            user, name, extra_info=extra_info, parent_task=parent_task
        )

        url = (
            url_for("pages.task", task_id=parent_task_id)
            if parent_task_id is not None
            else url_for("pages.active_tasks")
        )
        return redirect(url)

    @form("/tasks/remove", "remove_task")
    @auth.has_access
    def _():
        form = request.form
        task_id = form["task_id"]

        task = Task.get_or_none(id=task_id, user_id=g.user_id)
        if task is None:
            abort(400)

        parent_task = task.parent_task

        task_usecase.remove_task(task)

        return redirect(
            url_for("pages.task", task_id=parent_task.id)
            if parent_task is not None
            else url_for("pages.active_tasks")
        )

    @form("/tasks/complete", "complete_task")
    @auth.has_access
    def _():
        form = request.form
        task_id = form["task_id"]

        task = Task.get_or_none(id=task_id, user_id=g.user_id)
        if task is None:
            abort(400)

        parent_task = task.parent_task

        task_usecase.complete_task(task)

        return redirect(
            url_for("pages.task", task_id=parent_task.id)
            if parent_task is not None
            else url_for("pages.active_tasks")
        )

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
