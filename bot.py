"""
Ilmkon School — Qayta Aloqa Boti
Aiogram 3 + SQLAlchemy 2.0 async

Ishga tushirish:
    pip install -r requirements.txt
    .env faylini to'ldiring (.env.example ga qarang)
    python bot.py
"""
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, ErrorEvent

from config import load_config
from database.repo import init_db, make_session_pool
from handlers import admin, broadcast, fallback, feedback, start
from middlewares.core import (
    ConfigMiddleware,
    DbSessionMiddleware,
    SubscriptionMiddleware,
    ThrottlingMiddleware,
)


def setup_logging() -> logging.Logger:
    """Konsol + bot.log fayliga yozish (fayl 5 MB dan oshsa aylanadi)."""
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    )
    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    console = logging.StreamHandler()
    console.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console])
    return logging.getLogger("ilmkon-bot")


logger = setup_logging()


async def on_error(event: ErrorEvent):
    """Kutilmagan xato — bot yiqilmaydi, log'ga yoziladi."""
    logger.exception("Xato: %s | Update: %s", event.exception, event.update)


async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Bosh menyu"),
        BotCommand(command="help", description="❓ Yordam"),
        BotCommand(command="admin", description="🛠 Admin panel"),
    ])


async def notify_admins(bot: Bot, admin_ids: list[int], text: str):
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass


async def main():
    config = load_config()
    session_pool, engine = make_session_pool(config.db_url)
    await init_db(engine)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middleware zanjiri: Throttling -> Config -> DB -> Subscription
    for observer in (dp.message, dp.callback_query):
        observer.middleware(ThrottlingMiddleware(rate=config.throttle_rate))
        observer.middleware(ConfigMiddleware(config))
        observer.middleware(DbSessionMiddleware(session_pool))
        observer.middleware(SubscriptionMiddleware())

    # DIQQAT: fallback eng oxirida bo'lishi shart!
    dp.include_routers(
        start.router,
        feedback.router,
        admin.router,
        broadcast.router,
        fallback.router,
    )
    dp.errors.register(on_error)

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot ishga tushdi ✅")
    await notify_admins(bot, config.admin_ids, "✅ Bot ishga tushdi")

    try:
        await dp.start_polling(bot)
    finally:
        await notify_admins(bot, config.admin_ids, "🔴 Bot to'xtatildi")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
