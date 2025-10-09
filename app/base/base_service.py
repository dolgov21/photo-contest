from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.web.app import Application


class BaseService(ABC):
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app

        app.on_startup.append(self.startup)
        app.on_shutdown.append(self.shutdown)

    @abstractmethod
    async def startup(self, app: "Application"):
        return

    @abstractmethod
    async def shutdown(self, app: "Application"):
        return
