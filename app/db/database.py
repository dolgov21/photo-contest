import typing
from typing import Any

from sqlalchemy import URL, Column, DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

if typing.TYPE_CHECKING:
    from app.config import DatabaseConfig
    from app.web.app import Application


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    @declared_attr
    def recorded_at(self):
        return Column(DateTime, default=func.now())


class Database:
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]

    def __init__(self, scraper: "Application"):
        self.scraper = scraper

    @staticmethod
    def get_db_url(config_db: "DatabaseConfig") -> str:
        return URL.create(
            drivername="postgresql+asyncpg",
            host=config_db.host,
            port=config_db.port,
            username=config_db.user,
            password=config_db.password,
            database=config_db.database,
        ).render_as_string(hide_password=False)

    async def connect(self, *args: Any, **kwargs: Any):
        self.engine = create_async_engine(
            url=self.get_db_url(self.scraper.config.database), echo=True
        )

        self.sessionmaker = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def disconnect(self, *args: Any, **kwargs: Any):
        await self.engine.dispose()


def setup_database(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
