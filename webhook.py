from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from .config import settings

def build_app(bot: Bot, dp: Dispatcher) -> web.Application:
    app = web.Application()

    handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=settings.webhook_secret)
    handler.register(app, path="/webhook")

    async def on_startup(app: web.Application):
        await bot.set_webhook(
            settings.webhook_url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True,
        )

    async def on_cleanup(app: web.Application):
        await bot.delete_webhook(drop_pending_updates=False)

    async def ping(_):
        return web.Response(text="ok")
    app.router.add_get("/", ping)

    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app
