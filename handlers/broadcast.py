"""
Reklama / ommaviy xabar yuborish.
Istalgan xabar nusxa (copy) qilib yuboriladi — kim yuborgani korinmaydi.
Xabar mazmuni emas, faqat joylashuvi (chat_id + message_id) saqlanadi.
"""
import asyncio

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from database.repo import Repo
from keyboards.inline import back_kb, broadcast_confirm_kb
from states.forms import BroadcastForm

router = Router()


@router.callback_query(F.data == "bc:start")
async def bc_start(call: CallbackQuery, state: FSMContext, config: Config):
    if not config.can_broadcast(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "📣 <b>Reklama yuborish</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni shu yerga tashlang "
        "(matn, rasm, video — istalgan format).\n\n"
        "Xabar barcha foydalanuvchilarga bot nomidan yuboriladi."
    )
    await state.set_state(BroadcastForm.waiting_message)
    await call.answer()


@router.message(BroadcastForm.waiting_message)
async def bc_got_message(message: Message, state: FSMContext, repo: Repo):
    await state.update_data(
        bc_chat_id=message.chat.id,
        bc_message_id=message.message_id,
    )
    count = len(await repo.all_active_user_ids())
    await message.answer(
        f"📬 Xabar <b>{count}</b> ta foydalanuvchiga yuboriladi.\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_kb(),
    )
    await state.set_state(BroadcastForm.confirm)


@router.callback_query(BroadcastForm.confirm, F.data == "bc:send")
async def bc_send(call: CallbackQuery, state: FSMContext, repo: Repo,
                  bot: Bot, config: Config):
    data = await state.get_data()
    await state.clear()
    await call.message.edit_text("🚀 Yuborilmoqda...")
    await call.answer()

    user_ids = await repo.all_active_user_ids()
    sent, failed = 0, 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=data["bc_chat_id"],
                message_id=data["bc_message_id"],
            )
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=data["bc_chat_id"],
                    message_id=data["bc_message_id"],
                )
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            await repo.mark_blocked(uid)
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(config.broadcast_delay)  # sozlanadigan interval

    await call.message.edit_text(
        f"📣 <b>Reklama yakunlandi</b>\n\n"
        f"✅ Yuborildi: <b>{sent}</b>\n"
        f"❌ Yetib bormadi: <b>{failed}</b>",
        reply_markup=back_kb(),
    )


@router.callback_query(BroadcastForm.confirm, F.data == "bc:cancel")
async def bc_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Reklama bekor qilindi.",
                                 reply_markup=back_kb())
    await call.answer()
