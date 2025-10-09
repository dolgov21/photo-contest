import asyncio
import typing
from asyncio import Future, Task

from loguru import logger

from app.base.base_service import BaseService
from app.poller.schemas import Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UpdatesHandler(BaseService):
    def __init__(self, app: "Application"):
        super().__init__(app)
        self.app = app

        self.last_update_id = 0
        self.is_running = False
        self.update_tasks: set[Task] = set()
        self.loop_handler_task: Task = None

    async def startup(self, app: "Application"):
        self.start()
        logger.info("UpdatesHandler running...")

    async def shutdown(self, app: "Application"):
        await self.stop()
        logger.info("UpdatesHandler stopped.")

    async def _process_update(self, update: Update):
        if update.message:
            await self.app.store.bot.send_message(
                chat_id=update.message.chat.id,
                text=update.message.text,
            )

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            logger.opt(exception=result.exception()).error(
                "Error with handling update"
            )
        self.update_tasks.discard(result)

    async def _loop_handler(self):
        while self.is_running:
            update = await self.app.updates_queue.get()
            update_task = asyncio.create_task(self._process_update(update))
            self.update_tasks.add(update_task)
            update_task.add_done_callback(self._done_callback)

    def start(self):
        self.is_running = True
        self.loop_handler_task = asyncio.create_task(self._loop_handler())

    async def stop(self):
        self.is_running = False
        logger.info("Stopping updates handler...")
        self.loop_handler_task.cancel()
        await asyncio.gather(*self.update_tasks, return_exceptions=True)


def setup_handler(app: "Application"):
    app.poller = UpdatesHandler(app)
