import datetime
from typing import Optional

from planner.core.models import Task
from planner.core.models import User
from planner.core.models import db


def create_task(
    user: User,
    name: str,
    extra_info: Optional[str] = None,
    parent_task: Optional[Task] = None,
) -> Task:
    with db.atomic():
        task = Task.create(
            user=user,
            parent_task=parent_task,
            name=name,
            extra_info=extra_info,
            progress=0,
            created_at=datetime.datetime.utcnow(),
        )

        if parent_task is not None:
            _recalculate_task_chain_progress(parent_task)

    return task


def remove_task(task: Task) -> None:
    with db.atomic():
        parent_task = task.parent_task
        task.delete_instance()

        if parent_task is not None:
            _recalculate_task_chain_progress(parent_task)


def complete_task(task: Task) -> None:
    with db.atomic():
        task.progress = 100.0
        task.save(only=[Task.progress])

        parent_task = task.parent_task
        if parent_task is not None:
            _recalculate_task_chain_progress(parent_task)


def _recalculate_task_chain_progress(task: Task) -> None:
    # fmt: off
    child_tasks = (
        Task
        .select(Task.id, Task.progress)
        .where(Task.parent_task == task)
        .dicts()
    )
    # fmt: on

    quantity = len(child_tasks)
    if quantity == 0:
        return

    total_child_tasks_progress = quantity * 100
    child_tasks_progress_sum = round(sum(i["progress"] for i in child_tasks), 2)
    progress = round((child_tasks_progress_sum / total_child_tasks_progress) * 100, 2)

    task.progress = progress
    task.save(only=[Task.progress])

    parent_task = task.parent_task
    if parent_task is not None:
        _recalculate_task_chain_progress(parent_task)
