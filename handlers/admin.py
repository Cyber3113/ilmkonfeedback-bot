"""Admin panel: murojaatga javob, yopish, Excel eksport, statistika."""
import os

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import Config
from database.repo import Repo
from keyboards.inline import admin_panel_kb, back_kb
from states.forms import AnswerForm
from utils.excel import export_appeals_excel

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, config: Config):
    if not config.can_broadcast(message.from_user.id):
        return
    await message.answer(
        "🛠 <b>Admin panel</b>",
        reply_markup=admin_panel_kb(
            can_export=config.is_admin(message.from_user.id)
        ),
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery, config: Config):
    if not config.can_broadcast(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "🛠 <b>Admin panel</b>",
        reply_markup=admin_panel_kb(
            can_export=config.is_admin(call.from_user.id)
        ),
    )
    await call.answer()


# ---------- Murojaatga javob berish (admin guruhdan) ----------
@router.callback_query(F.data.startswith("reply:"))
async def start_reply(call: CallbackQuery, state: FSMContext, config: Config):
    if not config.can_broadcast(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    public_id = call.data.split(":")[1]
    await state.update_data(reply_public_id=public_id,
                            admin_msg_id=call.message.message_id)
    await call.message.reply(
        f"✍️ <code>{public_id}</code> uchun javob matnini yozing "
        f"(shu xabarga <b>reply</b> qilib):"
    )
    await state.set_state(AnswerForm.waiting_answer)
    await call.answer()


@router.message(AnswerForm.waiting_answer, F.text)
async def send_answer(message: Message, state: FSMContext, repo: Repo,
                      bot: Bot):
    data = await state.get_data()
    public_id = data["reply_public_id"]
    appeal = await repo.get_appeal_by_public_id(public_id)
    if not appeal:
        await message.answer("❌ Murojaat topilmadi.")
        await state.clear()
        return

    await repo.answer_appeal(appeal, message.text.strip())

    # Foydalanuvchiga javobni yuborish
    user = appeal.user
    try:
        await bot.send_message(
            user.tg_id,
            f"💬 <b>Murojaatingizga javob keldi!</b>\n\n"
            f"🆔 <code>{appeal.public_id}</code>\n\n"
            f"<blockquote>{message.text.strip()}</blockquote>",
        )
        await message.answer(f"✅ Javob yuborildi: <code>{public_id}</code>")
    except Exception:
        await message.answer(
            f"⚠️ Javob saqlandi, lekin foydalanuvchi botni bloklagan "
            f"bo'lishi mumkin: <code>{public_id}</code>"
        )
    await state.clear()


@router.callback_query(F.data.startswith("close:"))
async def close_appeal(call: CallbackQuery, repo: Repo, config: Config,
                       bot: Bot):
    if not config.can_broadcast(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    public_id = call.data.split(":")[1]
    appeal = await repo.get_appeal_by_public_id(public_id)
    if not appeal:
        await call.answer("Topilmadi", show_alert=True)
        return
    await repo.close_appeal(appeal)
    await call.answer(f"🔒 {public_id} yopildi", show_alert=True)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.reply(f"🔒 <code>{public_id}</code> yopildi.")
    except Exception:
        pass
    try:
        await bot.send_message(
            appeal.user.tg_id,
            f"🔒 Murojaatingiz yopildi: <code>{public_id}</code>",
        )
    except Exception:
        pass


# ---------- Excel eksport (faqat adminlar) ----------
@router.callback_query(F.data == "export_excel")
async def export_excel(call: CallbackQuery, repo: Repo, config: Config):
    if not config.is_admin(call.from_user.id):
        await call.answer("⛔️ Faqat adminlar uchun", show_alert=True)
        return
    await call.answer("📊 Hisobot tayyorlanmoqda...")
    appeals = await repo.all_appeals()
    users = await repo.users_with_appeal_counts()
    stats = await repo.stats()
    path = export_appeals_excel(appeals, users, stats)
    await call.message.answer_document(
        FSInputFile(path),
        caption="📊 <b>Ilmkon School — Murojaatlar hisoboti</b>",
    )
    os.remove(path)


# ---------- Statistika ----------
@router.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery, repo: Repo, config: Config):
    if not config.is_admin(call.from_user.id):
        await call.answer("⛔️ Faqat adminlar uchun", show_alert=True)
        return
    s = await repo.stats()
    await call.message.edit_text(
        "📈 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{s['total_users']}</b>\n"
        f"📨 Jami murojaatlar: <b>{s['total_appeals']}</b>\n\n"
        f"💡 Takliflar: {s['by_type']['taklif']}\n"
        f"⚠️ E'tirozlar: {s['by_type']['etiroz']}\n\n"
        f"⏳ Ko'rib chiqilmoqda: {s['by_status']['pending']}\n"
        f"✅ Javob berildi: {s['by_status']['answered']}\n"
        f"🔒 Yopildi: {s['by_status']['closed']}",
        reply_markup=back_kb(),
    )
    await call.answer()
