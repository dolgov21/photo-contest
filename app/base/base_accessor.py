from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.web.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app

        app.on_startup.append(self.connect)
        app.on_shutdown.append(self.disconnect)

    @abstractmethod
    async def connect(self):
        return

    @abstractmethod
    async def disconnect(self):
        return
