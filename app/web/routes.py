from aiohttp.web_app import Application


def setup_routes(application: Application):
    from app.admin.routes import register_urls as register_admins_urls

    register_admins_urls(application)
