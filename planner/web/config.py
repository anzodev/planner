from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class Config:
    SECRET_KEY: str
    DB_PATH: str
    PBKDF2_PWD_HASHER_HASH_FUNC: str
    PBKDF2_PWD_HASHER_ITERATIONS: int
    PBKDF2_PWD_HASHER_SALT_LENGTH: int
    COMPLETED_TASKS_LIMIT: int
    LOCAL_RUN_HOST: str
    LOCAL_RUN_PORT: int

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        env = Env()
        env.read_env(env_path)

        with env.prefixed("PLANNER_"):
            return cls(
                SECRET_KEY=env.str("SECRET_KEY"),
                DB_PATH=env.str("DB_PATH"),
                PBKDF2_PWD_HASHER_HASH_FUNC=env.str("PBKDF2_PWD_HASHER_HASH_FUNC"),
                PBKDF2_PWD_HASHER_ITERATIONS=env.int("PBKDF2_PWD_HASHER_ITERATIONS"),
                PBKDF2_PWD_HASHER_SALT_LENGTH=env.int("PBKDF2_PWD_HASHER_SALT_LENGTH"),
                COMPLETED_TASKS_LIMIT=env.int("COMPLETED_TASKS_LIMIT", 10),
                LOCAL_RUN_HOST=env.str("LOCAL_RUN_HOST", "localhost"),
                LOCAL_RUN_PORT=env.int("LOCAL_RUN_PORT", 5000),
            )
