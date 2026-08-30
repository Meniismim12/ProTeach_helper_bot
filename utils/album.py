"""Albom (media group) yig'uvchi middleware.

Telegram albomni bir nechta alohida xabar qilib yuboradi — ularning
`media_group_id` si bir xil bo'ladi. Bu middleware birinchi xabarni ushlab
turadi, qolganlarini yig'adi va handler'ga `album` ro'yxatini uzatadi.
Albomning 2-, 3-, ... xabarlari handler'ga umuman yetib bormaydi.
"""

import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import ALBUM_LATENCY


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: float = ALBUM_LATENCY) -> None:
        self.latency = latency
        self.cache: dict[str, list[Message]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.media_group_id is None:
            data["album"] = None
            return await handler(event, data)

        key = event.media_group_id
        # asyncio bitta oqimda ishlagani uchun bu ikki qator atomik hisoblanadi
        bucket = self.cache.setdefault(key, [])
        bucket.append(event)
        if len(bucket) > 1:
            return None  # birinchi xabar allaqachon kutmoqda

        await asyncio.sleep(self.latency)

        messages = self.cache.pop(key, [])
        messages.sort(key=lambda m: m.message_id)
        data["album"] = messages
        return await handler(messages[0], data)
