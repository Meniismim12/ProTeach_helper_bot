"""/start, /cancel, /id va bosh menyu."""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from keyboards.inline import back_menu_kb, main_menu
from utils.ui import safe_edit

router = Router(name="start")

GREETING = (
    "👋 Assalomu alaykum, <b>{name}</b>!\n\n"
    "Men <b>e'lon tarqatuvchi</b> botman. Meni kerakli kanallarga admin qilib "
    "qo'shsangiz, bitta e'lonni bir vaqtda barcha kanallarga yuboraman.\n\n"
    "Quyidagi menyudan tanlang 👇"
)

HELP = (
    "ℹ️ <b>Qanday ishlaydi</b>\n\n"
    "<b>1. Kanalni ulash</b>\n"
    "Botni kanalingizga qo'shing va <b>administrator</b> qiling "
    "(«Post yuborish» huquqi yoqilgan bo'lsin). Bot kanalni o'zi ro'yxatga oladi — "
    "hech qanday ID kiritish shart emas.\n\n"
    "<b>2. E'lon yuborish</b>\n"
    "«📢 E'lon yuborish» → e'lonni botga yuboring (matn, rasm, video, fayl yoki albom) → "
    "xohlasangiz tugma qo'shing → kanallarni tanlang → ko'rib chiqing → yuboring.\n\n"
    "<b>Tugmalar formati</b>\n"
    "<code>Kursga yozilish - https://t.me/misol\n"
    "Sayt - https://misol.uz | Instagram - @misol</code>\n"
    "Har bir qator — alohida tugmalar qatori, <code>|</code> bitta qatorga bir nechta tugma qo'yadi.\n\n"
    "<b>Buyruqlar</b>\n"
    "/start — bosh menyu\n"
    "/cancel — joriy amalni bekor qilish\n"
    "/id — o'z Telegram ID ingizni ko'rish\n\n"
    "⚠️ Telegram albom (bir nechta rasm) ostiga tugma qo'yishga ruxsat bermaydi — "
    "u holda tugmalar albomdan keyingi alohida xabarda ketadi."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        GREETING.format(name=message.from_user.full_name),
        reply_markup=main_menu(is_owner=message.from_user.id == OWNER_ID),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    text = "❌ Bekor qilindi." if current else "Bekor qiladigan amal yo'q."
    await message.answer(
        text, reply_markup=main_menu(is_owner=message.from_user.id == OWNER_ID)
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(
        f"👤 Sizning ID: <code>{message.from_user.id}</code>\n"
        f"💬 Chat ID: <code>{message.chat.id}</code>"
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        call,
        GREETING.format(name=call.from_user.full_name),
        main_menu(is_owner=call.from_user.id == OWNER_ID),
    )
    await call.answer()


@router.callback_query(F.data == "flow:cancel")
async def cancel_flow(call: CallbackQuery, state: FSMContext) -> None:
    """Har qanday bosqichdan chiqish uchun umumiy tugma."""
    await state.clear()
    await safe_edit(
        call,
        "❌ Bekor qilindi.\n\n" + GREETING.format(name=call.from_user.full_name),
        main_menu(is_owner=call.from_user.id == OWNER_ID),
    )
    await call.answer()


@router.callback_query(F.data == "menu:help")
async def show_help(call: CallbackQuery) -> None:
    await safe_edit(call, HELP, back_menu_kb())
    await call.answer()
