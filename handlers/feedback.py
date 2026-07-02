"""Taklif va e'tiroz yuborish oqimi."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from database.models import AppealStatus, AppealType
from database.repo import Repo
from keyboards.inline import (
    admin_appeal_kb,
    anonymous_kb,
    back_kb,
    confirm_appeal_kb,
)
from states.forms import FeedbackForm

router = Router()

TYPE_NAMES = {"taklif": "💡 Taklif", "etiroz": "⚠️ E'tiroz"}
STATUS_NAMES = {
    AppealStatus.PENDING.value: "⏳ Ko'rib chiqilmoqda",
    AppealStatus.ANSWERED.value: "✅ Javob berildi",
    AppealStatus.CLOSED.value: "🔒 Yopildi",
}


@router.callback_query(F.data.startswith("new:"))
async def new_appeal(call: CallbackQuery, state: FSMContext):
    appeal_type = call.data.split(":")[1]
    await state.update_data(appeal_type=appeal_type)
    await call.message.edit_text(
        f"{TYPE_NAMES[appeal_type]} — murojaat qanday yuborilsin?",
        reply_markup=anonymous_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("anon:"))
async def choose_anon(call: CallbackQuery, state: FSMContext):
    is_anon = call.data.split(":")[1] == "yes"
    await state.update_data(is_anonymous=is_anon)
    data = await state.get_data()
    await call.message.edit_text(
        f"{TYPE_NAMES[data['appeal_type']]}\n\n"
        "✍️ Murojaat matnini yozib yuboring:"
    )
    await state.set_state(FeedbackForm.waiting_text)
    await call.answer()


@router.message(FeedbackForm.waiting_text, F.text)
async def got_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 10:
        await message.answer(
            "❗️ Murojaat juda qisqa. Kamida 10 ta belgi yozing."
        )
        return
    await state.update_data(text=text)
    data = await state.get_data()
    anon = "🕶 Anonim" if data["is_anonymous"] else "👤 Ism bilan"
    await message.answer(
        f"{TYPE_NAMES[data['appeal_type']]} | {anon}\n\n"
        f"<blockquote>{text}</blockquote>\n\n"
        "Yuborishni tasdiqlaysizmi?",
        reply_markup=confirm_appeal_kb(),
    )
    await state.set_state(FeedbackForm.confirm)


@router.callback_query(FeedbackForm.confirm, F.data == "appeal:send")
async def send_appeal(call: CallbackQuery, state: FSMContext, repo: Repo,
                      config: Config, bot: Bot):
    data = await state.get_data()
    user = await repo.get_user(call.from_user.id)
    appeal = await repo.create_appeal(
        user=user,
        appeal_type=data["appeal_type"],
        text=data["text"],
        is_anonymous=data["is_anonymous"],
    )
    await state.clear()

    # Foydalanuvchiga tasdiq
    await call.message.edit_text(
        f"✅ <b>Murojaatingiz qabul qilindi!</b>\n\n"
        f"🆔 Raqam: <code>{appeal.public_id}</code>\n"
        f"⏱ Javob 48 soat ichida beriladi.",
        reply_markup=back_kb(),
    )
    await call.answer()

    # Admin guruhga yuborish
    if data["is_anonymous"]:
        who = "🕶 <i>Anonim</i>"
    else:
        who = (f"👤 {user.full_name}\n📱 {user.phone}\n"
               f"🔗 <a href='tg://user?id={user.tg_id}'>Profil</a>")

    admin_text = (
        f"🆕 {TYPE_NAMES[appeal.type]}\n"
        f"🆔 <code>{appeal.public_id}</code>\n\n"
        f"{who}\n\n"
        f"<blockquote>{appeal.text}</blockquote>"
    )
    try:
        await bot.send_message(
            config.admin_group_id,
            admin_text,
            reply_markup=admin_appeal_kb(appeal.public_id),
        )
    except Exception:
        pass  # guruh sozlanmagan bo'lsa bot yiqilmasin


@router.callback_query(F.data == "my_appeals")
async def my_appeals(call: CallbackQuery, repo: Repo):
    user = await repo.get_user(call.from_user.id)
    appeals = await repo.my_appeals(user)
    if not appeals:
        await call.message.edit_text(
            "📭 Sizda hali murojaatlar yo'q.", reply_markup=back_kb()
        )
        await call.answer()
        return

    lines = ["📋 <b>Mening murojaatlarim</b>\n"]
    for a in appeals[:15]:
        lines.append(
            f"🆔 <code>{a.public_id}</code> | {TYPE_NAMES[a.type]}\n"
            f"   {STATUS_NAMES[a.status]} | "
            f"{a.created_at.strftime('%d.%m.%Y')}"
        )
        if a.answer:
            lines.append(f"   💬 <i>{a.answer[:100]}</i>")
    await call.message.edit_text("\n".join(lines), reply_markup=back_kb())
    await call.answer()
