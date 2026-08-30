"""Hech bir handler'ga tushmagan xabarlar.

Bu router eng oxirida ulanadi — undan oldingi barcha routerlar o'z xabarini
olib bo'lgandan keyingina bu yerga yetib keladi.
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import OWNER_ID
from keyboards.inline import main_menu

router = Router(name="fallback")


@router.message()
async def unknown(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        # Bosqich ichidamiz, lekin xabar turi mos emas
        await message.answer(
            "🤔 Hozir bunday xabar kutilmayapti.\n"
            "Yuqoridagi tugmalardan birini tanlang yoki /cancel bosing."
        )
        return

    await message.answer(
        "🤔 Tushunmadim. Quyidagi menyudan tanlang:",
        reply_markup=main_menu(is_owner=message.from_user.id == OWNER_ID),
    )
