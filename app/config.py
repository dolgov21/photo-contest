from dataclasses import dataclass
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from pyaml_env import parse_config

if TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class BotConfig:
    token: str
    timeout: int = 25


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    database: DatabaseConfig
    bot: BotConfig


def load_config(config_path: str) -> Config:
    load_dotenv()
    raw_config = parse_config(config_path)

    return Config(
        database=DatabaseConfig(
            host=raw_config["database"]["host"],
            port=raw_config["database"]["port"],
            user=raw_config["database"]["user"],
            password=raw_config["database"]["password"],
            database=raw_config["database"]["database"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            timeout=raw_config["bot"]["timeout"],
        ),
    )


def setup_config(app: "Application", config_path: str) -> "Application":
    app.config = load_config(config_path)
