"""
Fallback — hech bir handler'ga tushmagan xabarlar.
MUHIM: bu router eng OXIRIDA ulanadi.

Ro'yxatdan o'tgan foydalanuvchi nima yozsa ham qayta so'ralmaydi —
to'g'ridan-to'g'ri bosh menyu ko'rsatiladi.
Ro'yxatdan o'tmagan bo'lsa — registratsiya boshlanadi (faqat bir marta).
"""
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import Config
from database.repo import Repo
from handlers.start import show_main_menu
from states.forms import Registration

router = Router()


@router.message()
async def fallback(message: Message, state: FSMContext, repo: Repo,
                   config: Config):
    user = await repo.get_user(message.from_user.id)
    if user:
        # Ro'yxatdan o'tgan — savolsiz menyu
        await show_main_menu(message, config, message.from_user.id)
        return

    # Ro'yxatdan o'tmagan — bir martalik registratsiya
    await message.answer(
        "📝 Botdan foydalanish uchun bir marta ro'yxatdan o'tamiz.\n\n"
        "<b>Ism-familiyangizni</b> kiriting:"
    )
    await state.set_state(Registration.full_name)
