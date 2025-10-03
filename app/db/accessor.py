import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class DatabaseAccessor:
    def __init__(self, app: "Application"):
        self.app = app
