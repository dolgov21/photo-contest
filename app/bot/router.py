import typing
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger

from app.poller.schemes import Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Router:
    def __init__(self):
        self._handlers: dict[
            str, Callable[["Application", Update], Awaitable[Any]]
        ] = {}
        self._callbacks: dict[
            str, Callable[["Application", Update], Awaitable[Any]]
        ] = {}
        self._callback_prefixes: dict[
            str, Callable[["Application", Update], Awaitable[Any]]
        ] = {}

    def command(self, name: str):
        def wrapper(func):
            self._handlers[f"/{name}"] = func
            return func

        return wrapper

    def callback(self, name: str):
        def wrapper(func):
            self._callbacks[name] = func
            return func

        return wrapper

    def callback_startswith(self, name: str):
        def wrapper(func):
            self._callback_prefixes[name] = func
            return func

        return wrapper

    async def handle(self, app: "Application", update: Update):
        if update.message and update.message.text:
            command = update.message.text.strip().split()[0]
            handler = self._handlers.get(command)
            if handler:
                await handler(app, update)
            else:
                logger.warning(f"Not found command handler: {command}")

        if update.callback_query and update.callback_query.data:
            data = update.callback_query.data

            handler = self._callbacks.get(data)
            if not handler:
                handler = self._callback_prefixes.get(data.split("_")[0])

            if handler:
                await handler(app, update)
            else:
                logger.warning(f"Not found callback handler: {data}")
