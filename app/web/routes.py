from aiohttp.web_app import Application


def setup_routes(application: Application):
    import app.users.routes

    app.users.routes.register_urls(application)
