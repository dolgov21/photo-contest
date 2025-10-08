import typing


if typing.TYPE_CHECKING:
    from app.web.app import Application

__all__ = ("register_urls",)


def register_urls(app: "Application"):
    from app.admin.views import AdminLoginView
    from app.admin.views import AdminCurrentView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
