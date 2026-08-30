"""Kichik UI yordamchilari."""

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

log = logging.getLogger(__name__)


async def edit_screen(
    call: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Xabarni JOYIDA almashtiradi va hech qachon yangi xabar yubormaydi.

    Kanal tanlash ekranlari uchun: har bir bosishda yangi xabar kelib
    chatni to'ldirib yubormasligi kerak.
    """
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        # "message is not modified" — foydalanuvchi bir tugmani ikki marta bosdi
        if "message is not modified" not in exc.message.lower():
            log.warning("Ekranni yangilab bo'lmadi: %s", exc.message)


async def safe_edit(
    call: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Xabarni tahrirlaydi; imkoni bo'lmasa (media yoki o'zgarmagan matn) yangisini yuboradi."""
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in exc.message.lower():
            return
        await call.message.answer(text, reply_markup=reply_markup)
