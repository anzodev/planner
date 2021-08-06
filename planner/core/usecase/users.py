from planner.core.models import User
from planner.core.security import PasswordHasher


def create_user(username: str, password_hasher: PasswordHasher, password: str) -> User:
    return User.create(
        username=username,
        password_hash=password_hasher.make_hash(password),
    )
