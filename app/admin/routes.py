import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application

__all__ = ("register_urls",)


def register_urls(app: "Application"):
    from app.admin.views import (
        AdminContestsView,
        AdminCreateUserView,
        AdminCurrentView,
        AdminDeleteContestView,
        AdminLoginView,
    )

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.create_user", AdminCreateUserView)
    app.router.add_view("/admin.contests", AdminContestsView)
    app.router.add_view("/admin.contest.delete", AdminDeleteContestView)
