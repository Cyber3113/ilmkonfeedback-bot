"""Reply klaviaturalar (faqat telefon Share Contact uchun)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish",
                            request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
