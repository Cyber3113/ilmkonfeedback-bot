"""
Inline klaviaturalar.
Telegram Bot API 9.4 rangli tugmalar (style: primary / success / danger).
aiogram >= 3.28.2 talab qilinadi.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Channel

# Eski aiogram versiyalarida ham ishlashi uchun style'ni ehtiyotkor qo'shamiz
def _btn(text: str, callback_data: str | None = None, url: str | None = None,
         style: str | None = None) -> InlineKeyboardButton:
    kwargs = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if style:
        try:
            return InlineKeyboardButton(**kwargs, style=style)
        except TypeError:
            pass  # aiogram versiyasi style'ni qo'llamasa, oddiy tugma
    return InlineKeyboardButton(**kwargs)


def subscription_kb(channels: list[Channel]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.row(_btn(f"📢 {ch.title}", url=ch.url, style="primary"))
    b.row(_btn("✅ A'zo bo'ldim — Tekshirish", callback_data="check_sub",
               style="success"))
    return b.as_markup()


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        _btn("💡 Taklif yuborish", callback_data="new:taklif", style="success"),
        _btn("⚠️ E'tiroz yuborish", callback_data="new:etiroz", style="danger"),
    )
    b.row(_btn("📋 Mening murojaatlarim", callback_data="my_appeals",
               style="primary"))
    b.row(_btn("ℹ️ Bot haqida", callback_data="about", style="primary"))
    if is_admin:
        b.row(_btn("🛠 Admin panel", callback_data="admin_panel"))
    return b.as_markup()


def anonymous_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        _btn("👤 Ism bilan", callback_data="anon:no", style="primary"),
        _btn("🕶 Anonim", callback_data="anon:yes", style="primary"),
    )
    b.row(_btn("❌ Bekor qilish", callback_data="cancel", style="danger"))
    return b.as_markup()


def confirm_appeal_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        _btn("✅ Yuborish", callback_data="appeal:send", style="success"),
        _btn("❌ Bekor qilish", callback_data="cancel", style="danger"),
    )
    return b.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn("⬅️ Bosh menyu", callback_data="main_menu", style="primary"))
    return b.as_markup()


def admin_appeal_kb(public_id: str) -> InlineKeyboardMarkup:
    """Admin guruhdagi murojaat ostidagi tugmalar."""
    b = InlineKeyboardBuilder()
    b.row(
        _btn("✍️ Javob berish", callback_data=f"reply:{public_id}",
             style="success"),
        _btn("🔒 Yopish", callback_data=f"close:{public_id}", style="danger"),
    )
    return b.as_markup()


def admin_panel_kb(can_export: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn("📣 Reklama yuborish", callback_data="bc:start", style="primary"))
    if can_export:
        b.row(_btn("📊 Excel hisobot", callback_data="export_excel",
                   style="success"))
        b.row(_btn("📈 Statistika", callback_data="stats", style="primary"))
    b.row(_btn("⬅️ Bosh menyu", callback_data="main_menu"))
    return b.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        _btn("🚀 Yuborish", callback_data="bc:send", style="success"),
        _btn("❌ Bekor qilish", callback_data="bc:cancel", style="danger"),
    )
    return b.as_markup()


def role_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn("👨‍👩‍👧 Ota-ona", callback_data="role:parent", style="primary"))
    b.row(_btn("🎓 O'quvchi", callback_data="role:student", style="primary"))
    b.row(_btn("👔 Xodim", callback_data="role:staff", style="primary"))
    return b.as_markup()
