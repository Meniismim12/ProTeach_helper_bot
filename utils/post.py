"""E'lonni tayyorlash va kanalga yetkazish."""

import asyncio
import logging
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import (
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from config import SEND_DELAY
from database.channels import deactivate_channel

log = logging.getLogger(__name__)

_MEDIA_CLASSES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}


def _caption(msg: Message) -> str | None:
    """Formatlashni saqlagan holda caption ni HTML ga o'giradi."""
    if msg.caption is None and msg.text is None:
        return None
    return msg.html_text


def media_from_message(msg: Message) -> dict[str, Any] | None:
    """Albom qismini saqlash uchun dict ko'rinishiga o'tkazadi."""
    caption = _caption(msg)

    if msg.photo:
        return {
            "type": "photo",
            "file_id": msg.photo[-1].file_id,
            "caption": caption,
            "spoiler": bool(msg.has_media_spoiler),
        }
    if msg.video:
        return {
            "type": "video",
            "file_id": msg.video.file_id,
            "caption": caption,
            "spoiler": bool(msg.has_media_spoiler),
        }
    if msg.document:
        return {"type": "document", "file_id": msg.document.file_id, "caption": caption}
    if msg.audio:
        return {"type": "audio", "file_id": msg.audio.file_id, "caption": caption}
    return None


def build_media(items: list[dict[str, Any]]) -> list[Any]:
    """Saqlangan dict lardan InputMedia ro'yxatini yasaydi."""
    media: list[Any] = []
    for item in items:
        cls = _MEDIA_CLASSES[item["type"]]
        kwargs: dict[str, Any] = {
            "media": item["file_id"],
            "caption": item.get("caption"),
            "parse_mode": ParseMode.HTML,
        }
        if item["type"] in ("photo", "video") and item.get("spoiler"):
            kwargs["has_spoiler"] = True
        media.append(cls(**kwargs))
    return media


def build_payload(message: Message, album: list[Message] | None) -> dict[str, Any] | None:
    """Adminning xabaridan e'lon ma'lumotini tuzadi."""
    if album:
        items = [m for m in (media_from_message(msg) for msg in album) if m]
        if not items:
            return None
        return {"kind": "album", "media": items}
    return {
        "kind": "single",
        "from_chat_id": message.chat.id,
        "message_id": message.message_id,
    }


async def deliver(
    bot: Bot,
    chat_id: int,
    post: dict[str, Any],
    markup: InlineKeyboardMarkup | None = None,
    album_text: str | None = None,
) -> None:
    """E'lonni bitta chatga yuboradi."""
    if post["kind"] == "single":
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=post["from_chat_id"],
            message_id=post["message_id"],
            reply_markup=markup,
        )
        return

    # Telegram albom ostiga inline tugma qo'yishga ruxsat bermaydi —
    # tugmalar keyingi alohida xabarda ketadi.
    await bot.send_media_group(chat_id=chat_id, media=build_media(post["media"]))
    if markup is not None:
        await bot.send_message(chat_id, album_text or "👇", reply_markup=markup)


async def broadcast(
    bot: Bot,
    post: dict[str, Any],
    markup: InlineKeyboardMarkup | None,
    channels: list[dict[str, Any]],
    album_text: str | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    """Barcha tanlangan kanallarga yuboradi. (muvaffaqiyatli, xatolar) qaytaradi."""
    sent: list[dict[str, Any]] = []
    failed: list[tuple[dict[str, Any], str]] = []

    for channel in channels:
        chat_id = channel["chat_id"]
        try:
            await deliver(bot, chat_id, post, markup, album_text)
            sent.append(channel)
        except TelegramRetryAfter as exc:
            log.warning("Flood limit: %s soniya kutilmoqda", exc.retry_after)
            await asyncio.sleep(exc.retry_after + 1)
            try:
                await deliver(bot, chat_id, post, markup, album_text)
                sent.append(channel)
            except Exception as retry_exc:  # noqa: BLE001
                failed.append((channel, str(retry_exc)))
        except TelegramForbiddenError:
            await deactivate_channel(chat_id)
            failed.append((channel, "bot kanaldan chiqarilgan"))
        except TelegramBadRequest as exc:
            message = exc.message.lower()
            if "not enough rights" in message or "chat not found" in message:
                await deactivate_channel(chat_id)
                failed.append((channel, "botda post yuborish huquqi yo'q"))
            else:
                failed.append((channel, exc.message))
        except Exception as exc:  # noqa: BLE001
            log.exception("Kanalga yuborishda kutilmagan xato: %s", chat_id)
            failed.append((channel, str(exc)))

        await asyncio.sleep(SEND_DELAY)

    return sent, failed
