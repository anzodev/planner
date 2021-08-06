import pytest

from planner.core.usecase import users as user_usecase


@pytest.mark.usefixtures("with_memory_database")
def test_create_user(sha1_password_hasher):
    user = user_usecase.create_user(
        username="john_doe",
        password_hasher=sha1_password_hasher,
        password="password",
    )

    assert user.username == "john_doe"
    assert user.password_hash == "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8"
