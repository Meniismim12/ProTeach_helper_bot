"""Kanallarni avtomatik ro'yxatga olish va boshqarish."""

import html
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import CallbackQuery, ChatMemberUpdated

from config import OWNER_ID
from database.admins import is_admin
from database.channels import (
    deactivate_channel,
    delete_channel,
    get_all_channels,
    get_channel,
    update_title,
    upsert_channel,
)
from keyboards.inline import (
    back_menu_kb,
    channel_delete_confirm_kb,
    channels_list_kb,
)
from utils.ui import safe_edit

router = Router(name="channels")
log = logging.getLogger(__name__)

_CHAT_TYPES = {"channel", "supergroup", "group"}
_LOST_STATUSES = {
    ChatMemberStatus.LEFT,
    ChatMemberStatus.KICKED,
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.RESTRICTED,
}

# Nechta kanal uchun Telegramdan jonli ma'lumot (obunachilar soni) olinsin.
# Har biri 2 ta API chaqiruv — ko'p kanalda ro'yxat sekinlashmasligi uchun.
DETAIL_LIMIT = 25
# Klaviaturadagi 🗑 tugmalari soni cheklovi.
BUTTON_LIMIT = 50
# Telegram xabari 4096 belgidan oshmasligi kerak.
TEXT_LIMIT = 3800


def _title(chat) -> str:
    return chat.title or chat.full_name or str(chat.id)


def _link(row) -> str:
    title = html.escape(row["title"] or "Nomsiz")
    if row["username"]:
        return f'<a href="https://t.me/{row["username"]}">{title}</a>'
    return title


async def _notify_owner(bot: Bot, text: str) -> None:
    try:
        await bot.send_message(OWNER_ID, text, disable_web_page_preview=True)
    except Exception:  # noqa: BLE001
        log.warning("Egaga xabar yuborib bo'lmadi (u botni ishga tushirmagan bo'lishi mumkin)")


# --------------------------------------------------------------------------- #
# Avtomatik ro'yxatga olish
# --------------------------------------------------------------------------- #
@router.my_chat_member(F.chat.type.in_(_CHAT_TYPES))
async def bot_status_changed(event: ChatMemberUpdated, bot: Bot) -> None:
    """Bot kanalga admin qilinganda / chiqarilganda ishlaydi."""
    chat = event.chat
    member = event.new_chat_member
    actor = event.from_user

    if member.status == ChatMemberStatus.ADMINISTRATOR:
        # Kanalni faqat botning admini ulay oladi — aks holda begonalarning
        # kanallari e'lon ro'yxatiga tushib qolardi.
        if actor is None or not await is_admin(actor.id):
            who = html.escape(actor.full_name) if actor else "Noma'lum"
            actor_id = actor.id if actor else "—"
            try:
                await bot.leave_chat(chat.id)
                left = "Bot kanaldan chiqib ketdi."
            except Exception:  # noqa: BLE001
                log.warning("Kanaldan chiqib bo'lmadi: %s", chat.id)
                left = "⚠️ Kanaldan chiqib bo'lmadi — uni qo'lda o'chiring."
            await _notify_owner(
                bot,
                "⛔️ <b>Ruxsatsiz urinish</b>\n\n"
                f"👤 {who} (<code>{actor_id}</code>)\n"
                f"📡 <b>{html.escape(_title(chat))}</b> (<code>{chat.id}</code>)\n\n"
                f"U botning admini emas. {left}",
            )
            log.warning("Ruxsatsiz kanal urinishi: %s (%s)", _title(chat), chat.id)
            return

        is_new = await upsert_channel(
            chat_id=chat.id,
            title=_title(chat),
            username=chat.username,
            chat_type=chat.type,
            added_by=actor.id,
        )
        can_post = getattr(member, "can_post_messages", None)
        warn = ""
        if chat.type == "channel" and can_post is False:
            warn = (
                "\n\n⚠️ Diqqat: botda «Post yuborish» huquqi yo'q. "
                "Kanal sozlamalaridan yoqing."
            )

        await _notify_owner(
            bot,
            f"{'➕ Yangi kanal ulandi' if is_new else '🔄 Kanal qayta faollashtirildi'}\n\n"
            f"📡 <b>{html.escape(_title(chat))}</b>\n"
            f"🆔 <code>{chat.id}</code>\n"
            f"👤 Qo'shdi: {html.escape(actor.full_name)}"
            f"{warn}",
        )
        log.info("Kanal ro'yxatga olindi: %s (%s)", _title(chat), chat.id)

    elif member.status in _LOST_STATUSES:
        row = await get_channel(chat.id)
        if row is None:
            return
        await deactivate_channel(chat.id)
        await _notify_owner(
            bot,
            "➖ Bot kanalda admin emas\n\n"
            f"📡 <b>{html.escape(_title(chat))}</b>\n"
            f"🆔 <code>{chat.id}</code>\n\n"
            "Bu kanal e'lon yuborish ro'yxatidan olib qo'yildi.",
        )
        log.info("Kanal o'chirildi: %s (%s)", _title(chat), chat.id)


# --------------------------------------------------------------------------- #
# Kanallar ro'yxati
# --------------------------------------------------------------------------- #
async def _render_channels(call: CallbackQuery, bot: Bot) -> None:
    """Ro'yxatni chizadi.

    Bu yerda `call.answer()` ataylab chaqirilmaydi — chaqiruvchi handler unga
    o'zi javob beradi. Bitta callback_query ga ikki marta javob berilsa
    Telegram xato qaytaradi.
    """
    channels = await get_all_channels()
    if not channels:
        await safe_edit(
            call,
            "📋 <b>Kanallar ro'yxati bo'sh</b>\n\n"
            "Botni kanalingizga qo'shing va <b>administrator</b> qiling — "
            "u avtomatik ro'yxatga tushadi.",
            back_menu_kb(),
        )
        return

    lines: list[str] = []
    active = 0
    for index, row in enumerate(channels, start=1):
        if not row["is_active"]:
            lines.append(f"{index}. 🔴 {_link(row)}\n    <code>{row['chat_id']}</code>")
            continue

        active += 1
        extra = ""
        title = _link(row)
        if index <= DETAIL_LIMIT:
            # Nomi o'zgargan bo'lishi mumkin — yangilab qo'yamiz
            try:
                chat = await bot.get_chat(row["chat_id"])
                if chat.title != row["title"] or chat.username != row["username"]:
                    await update_title(row["chat_id"], chat.title or "", chat.username)
                count = await bot.get_chat_member_count(row["chat_id"])
                extra = f" · 👥 {count}"
                title = html.escape(chat.title or "Nomsiz")
                if chat.username:
                    title = f'<a href="https://t.me/{chat.username}">{title}</a>'
            except Exception:  # noqa: BLE001
                extra = " · ⚠️ ma'lumot olinmadi"
        lines.append(f"{index}. 🟢 {title}{extra}\n    <code>{row['chat_id']}</code>")

    header = f"📋 <b>Kanallar</b> — jami {len(channels)} ta, faol {active} ta\n\n"
    footer = (
        "\n\n🟢 faol · 🔴 bot admin emas\n"
        "Ro'yxatdan olib tashlash uchun 🗑 tugmasini bosing."
    )

    body = ""
    for shown, line in enumerate(lines):
        if len(header) + len(body) + len(line) + len(footer) > TEXT_LIMIT:
            body += f"\n… va yana {len(lines) - shown} ta (ro'yxat juda uzun)"
            break
        body += ("\n" if body else "") + line

    await safe_edit(
        call,
        header + body + footer,
        channels_list_kb([dict(row) for row in channels[:BUTTON_LIMIT]]),
    )


@router.callback_query(F.data == "ch:list")
async def show_channels(call: CallbackQuery, bot: Bot) -> None:
    await call.answer("Yangilanmoqda…")
    await _render_channels(call, bot)


@router.callback_query(F.data.startswith("ch:del:"))
async def ask_delete(call: CallbackQuery) -> None:
    chat_id = int(call.data.removeprefix("ch:del:"))
    row = await get_channel(chat_id)
    if row is None:
        await call.answer("Bu kanal allaqachon o'chirilgan", show_alert=True)
        return
    await safe_edit(
        call,
        f"🗑 <b>{html.escape(row['title'] or 'Nomsiz')}</b> kanalini ro'yxatdan o'chirasizmi?\n\n"
        "Bot kanalning o'zidan chiqmaydi — faqat e'lon ro'yxatidan olinadi.",
        channel_delete_confirm_kb(chat_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ch:delyes:"))
async def do_delete(call: CallbackQuery, bot: Bot) -> None:
    chat_id = int(call.data.removeprefix("ch:delyes:"))
    await delete_channel(chat_id)
    await call.answer("O'chirildi ✅")
    await _render_channels(call, bot)
