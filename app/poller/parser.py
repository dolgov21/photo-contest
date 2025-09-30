import typing

from loguru import logger

from app.poller.schemas import Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UpdatesParser:
    def __init__(self, app: "Application"):
        self.app = app

    def _create_update(self, update: dict) -> Update | None:
        message = update.get("message")

        if not message:
            return None

        return Update(
            update_id=update["update_id"], payload=update["message"]["text"]
        )

    def parse_data(self, data: dict):
        updates = data.get("result", [])
        for update in updates:
            update_object = self._create_update(update)
            if update_object:
                self.app.updates_queue.put_nowait(update_object)
        logger.debug(f"Updates in queue: {self.app.updates_queue}")
