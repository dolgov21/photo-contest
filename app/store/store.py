import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.admin.accessor import AdminAccessor
        from app.bot.accessor import BotAccessor
        from app.db.accessor import DatabaseAccessor
        from app.services.tournament import TournamentService

        self.bot = BotAccessor(app)
        self.db = DatabaseAccessor(app)
        self.admin = AdminAccessor(app)
        self.services = TournamentService(app)


def setup_store(app: "Application"):
    app.store = Store(app)
    app.on_startup.append(app.store.admin.connect)
