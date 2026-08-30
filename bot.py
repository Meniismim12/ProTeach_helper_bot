"""Kanallarga e'lon tarqatuvchi Telegram bot.

Ikki rejimda ishlaydi:

* **polling** — lokal kompyuter yoki VPS (standart holat)
* **webhook** — Render va shunga o'xshash hostinglar. `WEBHOOK_BASE_URL` yoki
  Render o'zi beradigan `RENDER_EXTERNAL_URL` mavjud bo'lsa avtomatik yoqiladi.

Ishga tushirish:
    python bot.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import (
    BOT_TOKEN,
    PORT,
    USE_WEBHOOK,
    WEBHOOK_BASE_URL,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
)
from database.db import close_db, init_db
from handlers import admins, channels, fallback, post, start
from middlewares.access import AccessMiddleware
from utils.album import AlbumMiddleware

log = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description="Bosh menyu"),
    BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
    BotCommand(command="id", description="Mening Telegram ID im"),
]


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: avval kirish nazorati — guruhdan yoki begonadan kelgan
    # xabar albom buferiga ham tushmasdan darhol tashlab yuboriladi.
    dp.message.outer_middleware(AccessMiddleware())
    dp.message.outer_middleware(AlbumMiddleware())
    dp.callback_query.outer_middleware(AccessMiddleware())

    dp.include_router(start.router)
    dp.include_router(channels.router)
    dp.include_router(admins.router)
    dp.include_router(post.router)
    dp.include_router(fallback.router)  # eng oxirida — qolgan hamma narsani ushlaydi
    return dp


async def _health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


def build_web_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """Webhook uchun aiohttp ilovasi (Telegramga hech qanday so'rov yubormaydi)."""
    app = web.Application()
    # Render ochiq portni shu yerdan tekshiradi; keep-alive ping ham shu manzilga
    app.router.add_get("/", _health)
    app.router.add_get("/healthz", _health)

    # secret_token — Telegramdan kelmagan so'rovlar 401 bilan rad etiladi
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(
        app, path=WEBHOOK_PATH
    )
    setup_application(app, dp, bot=bot)
    return app


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    """Render uchun: HTTP server ochib, Telegram so'rovlarini kutadi."""
    url = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(
        url=url,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    log.info("Webhook o'rnatildi: %s", url)

    runner = web.AppRunner(build_web_app(bot, dp))
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    log.info("HTTP server tinglayapti: 0.0.0.0:%s", PORT)

    try:
        await asyncio.Event().wait()  # abadiy ishlaydi
    finally:
        await runner.cleanup()


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    """Lokal / VPS uchun: Telegramdan yangiliklarni o'zi so'rab turadi."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    try:
        me = await bot.get_me()
        log.info(
            "Bot ishga tushdi: @%s (id=%s) — %s rejimi",
            me.username,
            me.id,
            "webhook" if USE_WEBHOOK else "polling",
        )

        # Buyruqlar menyusi faqat shaxsiy chatda ko'rinsin — guruhlarda bot
        # umuman ko'zga tashlanmasligi kerak.
        await bot.delete_my_commands()
        await bot.set_my_commands(COMMANDS, scope=BotCommandScopeAllPrivateChats())

        if USE_WEBHOOK:
            await run_webhook(bot, dp)
        else:
            await run_polling(bot, dp)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot to'xtatildi")
