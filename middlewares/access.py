"""Botga kirish nazorati.

Ikkita qat'iy qoida:

1. **Bot faqat shaxsiy chatda javob beradi.** Guruh, supergruppa yoki kanaldan
   kelgan xabar/tugma bosishlari jimgina tashlab yuboriladi. Bot kanalga
   faqat bitta holatda yozadi — admin e'lon tarqatganda (`utils/post.py`).

2. **Faqat adminlar.** Begona odamga hech qanday javob qaytarilmaydi — na matn,
   na ogohlantirish. U bot borligini ham bilmaydi; urinish faqat logga tushadi.
"""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import TelegramObject

from database.admins import is_admin

log = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat = data.get("event_chat")
        user = data.get("event_from_user")

        # 1. Shaxsiy chatdan tashqarida bot butunlay jim.
        if chat is None or chat.type != ChatType.PRIVATE:
            if chat is not None:
                log.debug(
                    "E'tiborsiz qoldirildi: %s chatidan xabar (%s)", chat.type, chat.id
                )
            return None

        if user is None:
            return None

        # 2. Faqat adminlar. Begonaga javob yo'q.
        if not await is_admin(user.id):
            log.info(
                "Ruxsatsiz urinish: %s (id=%s)",
                user.full_name,
                user.id,
            )
            return None

        return await handler(event, data)
