"""
To'rtta middleware:
1. ThrottlingMiddleware — spam himoya: 1 foydalanuvchi / 1 soniya
2. ConfigMiddleware  — config'ni har handler'ga uzatadi
3. DbSessionMiddleware — har update uchun DB session ochadi
4. SubscriptionMiddleware — majburiy kanal a'zoligini tekshiradi
"""
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import Config
from database.repo import Repo
from keyboards.inline import subscription_kb


class ThrottlingMiddleware(BaseMiddleware):
    """
    Har foydalanuvchidan soniyasiga 1 ta xabar qabul qilinadi.
    Tez-tez bosilgan xabarlar jimgina e'tiborsiz qoldiriladi —
    bot ortiqcha yuklanmaydi va spamdan himoyalanadi.
    """

    def __init__(self, rate: float = 1.0):
        self.rate = rate
        self._last_seen: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_seen.get(user.id, 0.0)
        if now - last < self.rate:
            # Juda tez — e'tiborsiz. Callback bo'lsa "yuklanish" belgisini o'chiramiz
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None
        self._last_seen[user.id] = now

        # Xotira o'sib ketmasligi uchun eski yozuvlarni tozalab turamiz
        if len(self._last_seen) > 10_000:
            cutoff = now - 60
            self._last_seen = {
                uid: t for uid, t in self._last_seen.items() if t > cutoff
            }

        return await handler(event, data)


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: Config):
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["repo"] = Repo(session)
            return await handler(event, data)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Foydalanuvchi barcha majburiy kanallarga a'zo bo'lmaguncha
    botdan foydalana olmaydi. Adminlar tekshiruvdan ozod.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        config: Config = data["config"]
        bot: Bot = data["bot"]

        # Kanallar sozlanmagan bo'lsa — tekshirilmaydi
        if not config.channels:
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        # Adminlar va operatorlar ozod
        if config.can_broadcast(user.id):
            return await handler(event, data)

        # "Tekshirish" tugmasi bosilganda handler ishlashi kerak
        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)

        not_joined = []
        for ch in config.channels:
            try:
                member = await bot.get_chat_member(ch.username, user.id)
                if member.status in ("left", "kicked"):
                    not_joined.append(ch)
            except Exception:
                # Bot kanalda admin bo'lmasa tekshira olmaydi — o'tkazib yuboramiz
                continue

        if not not_joined:
            return await handler(event, data)

        text = (
            "🔒 <b>Botdan foydalanish uchun quyidagi kanal(lar)ga a'zo bo'ling:</b>\n\n"
            + "\n".join(f"• {ch.title}" for ch in not_joined)
            + "\n\nA'zo bo'lgach, <b>«✅ A'zo bo'ldim»</b> tugmasini bosing."
        )
        kb = subscription_kb(config.channels)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.answer("Avval kanallarga a'zo bo'ling!", show_alert=True)
            if event.message:
                try:
                    await event.message.edit_text(text, reply_markup=kb)
                except Exception:
                    await event.message.answer(text, reply_markup=kb)
        return None
