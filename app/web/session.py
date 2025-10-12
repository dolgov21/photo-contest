import base64
import typing

from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_session(app: "Application"):
    key_str = app.config.session.key
    key_bytes = base64.urlsafe_b64decode(key_str)

    storage = EncryptedCookieStorage(key_bytes)

    setup(app, storage)
