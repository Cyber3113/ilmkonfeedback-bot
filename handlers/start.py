"""Start, a'zolik tekshiruvi, registratsiya va bosh menyu."""
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import Config
from database.repo import Repo
from keyboards.inline import back_kb, main_menu_kb, role_kb
from keyboards.reply import phone_kb
from states.forms import Registration

router = Router()

WELCOME = (
    "👋 <b>Assalomu alaykum!</b>\n\n"
    "Bu — <b>Ilmkon School Qayta Aloqa Boti</b>.\n"
    "Bu yerda maktab faoliyati bo'yicha <b>taklif</b> va "
    "<b>e'tiroz</b>laringizni yuborishingiz mumkin. Har bir murojaat "
    "rahbariyatga yetib boradi va javob qaytariladi."
)


async def show_main_menu(message: Message, config: Config, user_id: int,
                         edit: bool = False):
    text = "🏠 <b>Bosh menyu</b>\n\nKerakli bo'limni tanlang:"
    kb = main_menu_kb(is_admin=config.can_broadcast(user_id))
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, repo: Repo,
                    config: Config):
    await state.clear()
    user = await repo.get_user(message.from_user.id)
    if user:
        # Ro'yxatdan o'tgan — hech narsa so'ramaymiz, to'g'ri menyu
        await show_main_menu(message, config, message.from_user.id)
        return

    await message.answer(WELCOME)
    await message.answer(
        "📝 Avval ro'yxatdan o'tamiz.\n\n"
        "<b>Ism-familiyangizni</b> kiriting:"
    )
    await state.set_state(Registration.full_name)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Yordam</b>\n\n"
        "💡 <b>Taklif</b> — maktabni yaxshilash bo'yicha fikringiz\n"
        "⚠️ <b>E'tiroz</b> — muammo yoki norozilik\n\n"
        "Har bir murojaatga unikal raqam beriladi va 48 soat "
        "ichida javob qaytariladi. Xohlasangiz anonim yuborishingiz mumkin.\n\n"
        "Buyruqlar:\n"
        "/start — bosh menyu\n"
        "/help — yordam"
    )


@router.message(Registration.full_name, F.text)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❗️ Iltimos, to'liq ism-familiya kiriting.")
        return
    await state.update_data(full_name=name)
    await message.answer(
        "📱 Telefon raqamingizni yuboring (pastdagi tugma orqali):",
        reply_markup=phone_kb(),
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("✅ Qabul qilindi.",
                         reply_markup=ReplyKeyboardRemove())
    await message.answer("👥 Kim sifatida murojaat qilasiz?",
                         reply_markup=role_kb())
    await state.set_state(Registration.role)


@router.message(Registration.phone)
async def reg_phone_invalid(message: Message):
    await message.answer(
        "❗️ Iltimos, pastdagi <b>«📱 Telefon raqamni yuborish»</b> "
        "tugmasidan foydalaning."
    )


@router.callback_query(Registration.role, F.data.startswith("role:"))
async def reg_role(call: CallbackQuery, state: FSMContext, repo: Repo,
                   config: Config):
    role = call.data.split(":")[1]
    data = await state.get_data()
    await repo.create_user(
        tg_id=call.from_user.id,
        full_name=data["full_name"],
        phone=data["phone"],
        role=role,
    )
    await state.clear()
    await call.message.edit_text("🎉 <b>Ro'yxatdan o'tdingiz!</b>")
    await show_main_menu(call.message, config, call.from_user.id)
    await call.answer()


@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, bot: Bot, config: Config, repo: Repo,
                    state: FSMContext):
    not_joined = []
    for ch in config.channels:
        try:
            member = await bot.get_chat_member(ch.username, call.from_user.id)
            if member.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception:
            continue

    if not_joined:
        await call.answer(
            "❌ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True
        )
        return

    await call.answer("✅ Rahmat! A'zolik tasdiqlandi.", show_alert=True)
    user = await repo.get_user(call.from_user.id)
    if user:
        await show_main_menu(call.message, config, call.from_user.id, edit=True)
    else:
        await call.message.edit_text(
            "📝 Endi ro'yxatdan o'tamiz.\n\n"
            "<b>Ism-familiyangizni</b> kiriting:"
        )
        await state.set_state(Registration.full_name)


@router.callback_query(F.data == "main_menu")
async def to_main_menu(call: CallbackQuery, state: FSMContext, config: Config):
    await state.clear()
    await show_main_menu(call.message, config, call.from_user.id, edit=True)
    await call.answer()


@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await call.message.edit_text(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "Ilmkon School rasmiy qayta aloqa boti.\n"
        "Taklif va e'tirozlaringiz to'g'ridan-to'g'ri maktab "
        "rahbariyatiga yetkaziladi.\n\n"
        "⏱ Javob muddati: 48 soat ichida.",
        reply_markup=back_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext, config: Config):
    await state.clear()
    await call.answer("Bekor qilindi")
    await show_main_menu(call.message, config, call.from_user.id, edit=True)
