"""Adminlarni boshqarish — faqat bot egasi (OWNER_ID) uchun."""

import html

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, MessageOriginUser

from config import OWNER_ID
from database.admins import add_admin, get_admins, remove_admin
from keyboards.inline import admins_list_kb, back_menu_kb, cancel_kb
from utils.ui import safe_edit

router = Router(name="admins")

# Butun router faqat egaga ochiq
router.message.filter(F.from_user.id == OWNER_ID)
router.callback_query.filter(F.from_user.id == OWNER_ID)


class AdminSG(StatesGroup):
    waiting_user = State()


def _admins_text(admins: list[dict]) -> str:
    if not admins:
        return (
            "👥 <b>Adminlar</b>\n\n"
            "Hozircha faqat siz (egasi) botni boshqarasiz.\n\n"
            "Yangi admin qo'shish uchun quyidagi tugmani bosing."
        )
    lines = []
    for index, admin in enumerate(admins, start=1):
        name = html.escape(admin["full_name"] or "Nomsiz")
        username = f" (@{admin['username']})" if admin["username"] else ""
        lines.append(f"{index}. {name}{username}\n    <code>{admin['user_id']}</code>")
    return (
        f"👥 <b>Adminlar</b> — {len(admins)} ta\n\n"
        + "\n".join(lines)
        + "\n\n🗑 tugmasi orqali adminlikdan olib tashlashingiz mumkin."
    )


async def _render_admins(call: CallbackQuery) -> None:
    """Ro'yxatni chizadi. `call.answer()` ataylab yo'q — chaqiruvchi handler
    unga o'zi javob beradi (bitta callback_query ga faqat bitta javob)."""
    admins = [dict(row) for row in await get_admins()]
    await safe_edit(call, _admins_text(admins), admins_list_kb(admins))


@router.callback_query(F.data == "adm:list")
async def show_admins(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    await _render_admins(call)


@router.callback_query(F.data == "adm:add")
async def ask_admin(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSG.waiting_user)
    await safe_edit(
        call,
        "➕ <b>Yangi admin</b>\n\n"
        "Quyidagilardan birini yuboring:\n"
        "• foydalanuvchining istalgan xabarini <b>forward</b> qiling;\n"
        "• yoki uning raqamli ID sini yozing (masalan <code>123456789</code>).\n\n"
        "ℹ️ <b>Forward eng qulayi</b> — bot begonalarga javob bermagani uchun "
        "u odam <code>/id</code> yozib o'z ID sini bila olmaydi.",
        cancel_kb(),
    )
    await call.answer()


@router.message(AdminSG.waiting_user)
async def got_admin(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id: int | None = None
    full_name = ""
    username: str | None = None

    origin = message.forward_origin
    if isinstance(origin, MessageOriginUser):
        user_id = origin.sender_user.id
        full_name = origin.sender_user.full_name
        username = origin.sender_user.username
    elif origin is not None:
        await message.answer(
            "❌ Bu foydalanuvchi forward xabarlarda profilini yashirgan.\n"
            "Undan raqamli ID sini so'rang (u botga <code>/id</code> yozsin) va shu yerga yuboring."
        )
        return
    elif message.text and message.text.strip().isdigit():
        user_id = int(message.text.strip())

    if user_id is None:
        await message.answer("❌ Tushunmadim. Xabarni forward qiling yoki raqamli ID yuboring.")
        return

    if user_id == OWNER_ID:
        await message.answer("ℹ️ Siz allaqachon bot egasisiz.")
        return

    if not full_name:
        try:
            chat = await bot.get_chat(user_id)
            full_name = chat.full_name or str(user_id)
            username = chat.username
        except Exception:  # noqa: BLE001
            full_name = str(user_id)

    await add_admin(user_id, full_name, username, added_by=OWNER_ID)
    await state.clear()

    try:
        await bot.send_message(
            user_id,
            "🎉 Sizga botda <b>admin</b> huquqi berildi!\n\n"
            "Boshlash uchun /start buyrug'ini yuboring.",
        )
    except Exception:  # noqa: BLE001
        pass

    admins = [dict(row) for row in await get_admins()]
    await message.answer(
        f"✅ <b>{html.escape(full_name)}</b> admin qilib qo'shildi.\n\n"
        + _admins_text(admins),
        reply_markup=admins_list_kb(admins),
    )


@router.callback_query(F.data.startswith("adm:del:"))
async def delete_admin(call: CallbackQuery, state: FSMContext) -> None:
    user_id = int(call.data.removeprefix("adm:del:"))
    await remove_admin(user_id)
    await state.clear()
    await call.answer("Adminlikdan olindi ✅")
    await _render_admins(call)


@router.callback_query(F.data == "adm:back")
async def back(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(call, "Bosh menyu", back_menu_kb())
    await call.answer()
