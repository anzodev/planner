import datetime
import hashlib
import secrets
from contextlib import contextmanager
from typing import Optional

import peewee as pw
import pytest

from planner.core.models import BaseModel
from planner.core.models import Task
from planner.core.models import User
from planner.core.models import db as models_db
from planner.core.security import PasswordHasher


class SHA1_PasswordHasher(PasswordHasher):
    def make_hash(self, password: str) -> str:
        return hashlib.sha1(password.encode("utf-8")).hexdigest()

    def is_hash_correct(self, password_hash: str, password: str) -> bool:
        return password_hash == self.make_hash(password)


@pytest.fixture
def sha1_password_hasher():
    return SHA1_PasswordHasher()


@pytest.fixture
def make_user(sha1_password_hasher):
    def _make_user(
        username: Optional[str] = None, password_hash: Optional[str] = None
    ) -> User:
        return User.create(
            username=f"test_{secrets.token_hex(8)}" if username is None else username,
            password_hash=(
                sha1_password_hasher.make_hash("password")
                if password_hash is None
                else password_hash
            ),
        )

    return _make_user


@pytest.fixture
def make_task(make_user):
    def _make_task(
        user: Optional[User] = None,
        parent_task: Optional[Task] = None,
        name: str = "Go for a walk",
        extra_info: Optional[str] = None,
        progress: float = 0.0,
        created_at: Optional[datetime.datetime] = None,
    ) -> Task:
        return Task.create(
            user=make_user() if user is None else user,
            parent_task=parent_task,
            name=name,
            extra_info=extra_info,
            progress=progress,
            created_at=datetime.datetime.utcnow() if created_at is None else created_at,
        )

    return _make_task


@pytest.fixture
def models() -> list[BaseModel]:
    return [User, Task]


@pytest.fixture
def models_db_init_context():
    @contextmanager
    def _models_db_init_context(db: pw.Database):
        origin_db = models_db.obj
        models_db.initialize(db)
        try:
            yield
        finally:
            models_db.initialize(origin_db)

    return _models_db_init_context


@pytest.fixture
def with_memory_database(models, models_db_init_context):
    db = pw.SqliteDatabase(":memory:")
    with models_db_init_context(db):
        db.create_tables(models)
        yield
