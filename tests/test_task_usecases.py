import datetime

import pytest

from planner.core.models import Task
from planner.core.usecase import tasks as task_usecase


@pytest.mark.usefixtures("with_memory_database")
@pytest.mark.freeze_time("2021-01-01 15:30:45")
def test_create_task(make_user):
    user = make_user()

    t1 = task_usecase.create_task(
        user=user,
        name="Go for a walk",
    )
    assert t1.user == user
    assert t1.parent_task is None
    assert t1.name == "Go for a walk"
    assert t1.extra_info is None
    assert t1.progress == 0
    assert t1.created_at == datetime.datetime(2021, 1, 1, 15, 30, 45)

    t2 = task_usecase.create_task(
        user=user,
        name="Go for a walk",
        extra_info="Make pause after long pc work.",
        parent_task=t1,
    )
    assert t2.user == user
    assert t2.parent_task == t1
    assert t2.name == "Go for a walk"
    assert t2.extra_info == "Make pause after long pc work."
    assert t2.progress == 0
    assert t2.created_at == datetime.datetime(2021, 1, 1, 15, 30, 45)


@pytest.mark.usefixtures("with_memory_database")
def test_remove_task(make_task):
    task = make_task()
    assert Task.select().count() == 1

    task_usecase.remove_task(task)
    assert Task.select().count() == 0


@pytest.mark.usefixtures("with_memory_database")
def test_complete_task(make_task):
    task = make_task()
    task_usecase.complete_task(task)

    assert task.progress == 100


@pytest.mark.usefixtures("with_memory_database")
def test_recalculate_task_chain_progress(make_user, make_task):
    user = make_user()
    parent_task = make_task(user=user)
    child_task1 = make_task(user=user, parent_task=parent_task)
    child_task2 = make_task(user=user, parent_task=parent_task)

    task_usecase._recalculate_task_chain_progress(parent_task)
    assert parent_task.progress == 0

    child_task1.progress = 50
    child_task1.save()

    task_usecase._recalculate_task_chain_progress(parent_task)
    assert parent_task.progress == 25

    child_task1.progress = 100
    child_task1.save()

    task_usecase._recalculate_task_chain_progress(parent_task)
    assert parent_task.progress == 50

    child_task2.progress = 100
    child_task2.save()

    task_usecase._recalculate_task_chain_progress(parent_task)
    assert parent_task.progress == 100


@pytest.mark.usefixtures("with_memory_database")
def test_recalculate_task_chain_progress__after_creation(make_user, make_task):
    user = make_user()
    parent_task = make_task(user=user, progress=100)
    make_task(user=user, parent_task=parent_task, progress=100)

    task_usecase.create_task(
        user=user,
        name="Go for a walk",
        parent_task=parent_task,
    )
    assert parent_task.progress == 50


@pytest.mark.usefixtures("with_memory_database")
def test_recalculate_task_chain_progress__after_removing(make_user, make_task):
    user = make_user()
    parent_task = make_task(user=user, progress=50)
    child_task = make_task(user=user, parent_task=parent_task, progress=100)
    make_task(user=user, parent_task=parent_task, progress=0)

    task_usecase.remove_task(child_task)
    assert parent_task.progress == 0


@pytest.mark.usefixtures("with_memory_database")
def test_recalculate_task_chain_progress__after_completion(make_user, make_task):
    user = make_user()
    parent_task = make_task(user=user, progress=50)
    child_task = make_task(user=user, parent_task=parent_task, progress=0)
    make_task(user=user, parent_task=parent_task, progress=100)

    task_usecase.complete_task(child_task)
    assert parent_task.progress == 100


@pytest.mark.usefixtures("with_memory_database")
def test_recalculate_task_chain_progress__long_task_chain_completion(
    make_user, make_task
):
    user = make_user()
    task1 = make_task(user=user)
    task2 = make_task(user=user, parent_task=task1)
    task3 = make_task(user=user, parent_task=task1)
    task4 = make_task(user=user, parent_task=task3)
    task5 = make_task(user=user, parent_task=task3)

    #       task1
    #      /     \
    # task2       task3
    #            /     \
    #       task4       task5

    for t in [task1, task2, task3, task4, task5]:
        assert t.progress == 0

    task_usecase.complete_task(task5)
    assert task1.progress == 25
    assert task2.progress == 0
    assert task3.progress == 50
    assert task4.progress == 0
    assert task5.progress == 100

    task_usecase.complete_task(task4)
    assert task1.progress == 50
    assert task2.progress == 0
    assert task3.progress == 100
    assert task4.progress == 100
    assert task5.progress == 100

    task_usecase.complete_task(task2)
    assert task1.progress == 100
    assert task2.progress == 100
    assert task3.progress == 100
    assert task4.progress == 100
    assert task5.progress == 100
