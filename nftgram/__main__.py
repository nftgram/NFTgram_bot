import asyncio
import functools
import logging
import json
import secrets

from aiohttp import web
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

import nftgram.handlers  # noqa: F401
from nftgram import config
from nftgram.database import database
from nftgram.bot import bot
from nftgram.i18n import _
from nftgram.bot import dp


async def handle_confirmed_token(request):
    try:
        body = await request.json()
        token_id = body["token_id"]
    except (json.JSONDecodeError, KeyError):
        return web.Response(status=400)
    data = json.loads(await database.get(f"token:{token_id}"))
    await bot.send_message(data["user_id"], _("token_confirmed"))
    return web.Response()


async def on_startup(*args, webhook_path=None):
    """Prepare bot before starting.

    Set webhook and run background tasks.
    """
    await database.connect(
        f"redis://{config.DATABASE_HOST}:{config.DATABASE_PORT}",
        password=config.DATABASE_PASSWORD,
    )
    app = web.Application()
    app.add_routes([web.post("/", handle_confirmed_token)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 2021)
    await site.start()
    await bot.delete_webhook()
    if webhook_path is not None:
        await bot.set_webhook("https://" + config.SERVER_HOST + webhook_path)


logging.basicConfig(level=config.LOGGER_LEVEL)
dp.middleware.setup(LoggingMiddleware())

if config.SET_WEBHOOK:
    url_token = secrets.token_urlsafe()
    webhook_path = config.WEBHOOK_PATH + "/" + url_token

    executor.start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=functools.partial(on_startup, webhook_path=webhook_path),
        host=config.INTERNAL_HOST,
        port=config.SERVER_PORT,
    )
else:
    executor.start_polling(
        dispatcher=dp, on_startup=on_startup, skip_updates=config.SKIP_UPDATES
    )
print()  # noqa: T001  Executor stopped with ^C

# Stop all background tasks
loop = asyncio.get_event_loop()
for task in asyncio.all_tasks(loop):
    task.cancel()
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
