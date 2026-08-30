"""Barcha inline klaviaturalar."""

from typing import Any, Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 E'lon yuborish", callback_data="post:new")
    kb.button(text="📋 Kanallar", callback_data="ch:list")
    if is_owner:
        kb.button(text="👥 Adminlar", callback_data="adm:list")
    kb.button(text="ℹ️ Yordam", callback_data="menu:help")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="menu:main")]]
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="flow:cancel")]]
    )


def ask_buttons_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Tugma qo'shish", callback_data="post:btn:yes")
    kb.button(text="➡️ Tugmasiz davom etish", callback_data="post:btn:no")
    kb.button(text="❌ Bekor qilish", callback_data="flow:cancel")
    kb.adjust(1)
    return kb.as_markup()


def skip_text_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ Matnsiz (faqat 👇)", callback_data="post:skip_text")
    kb.button(text="❌ Bekor qilish", callback_data="flow:cancel")
    kb.adjust(1)
    return kb.as_markup()


def _short(title: str, limit: int = 28) -> str:
    title = title or "Nomsiz"
    return title if len(title) <= limit else title[: limit - 1] + "…"


def channels_menu_kb() -> InlineKeyboardMarkup:
    """Kanal tanlash bosqichining bosh menyusi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="☑️ Hammasi", callback_data="sel:all")
    kb.button(text="📡 Kanallar tanlash", callback_data="sel:open")
    kb.button(text="👀 Ko'rib chiqish", callback_data="sel:done")
    kb.button(text="❌ Bekor qilish", callback_data="flow:cancel")
    kb.adjust(1)
    return kb.as_markup()


def channels_select_kb(
    channels: Iterable[dict[str, Any]],
    selected: set[int],
) -> InlineKeyboardMarkup:
    """Kanallar ro'yxati: har bir bosish belgini almashtiradi."""
    kb = InlineKeyboardBuilder()
    for channel in channels:
        mark = "✅" if channel["chat_id"] in selected else "⬜️"
        kb.button(
            text=f"{mark} {_short(channel['title'])}",
            callback_data=f"sel:t:{channel['chat_id']}",
        )
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="✔️ Tayyor", callback_data="sel:back"))
    return kb.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Yuborish", callback_data="post:send")
    kb.button(text="⬅️ Kanallarni o'zgartirish", callback_data="post:back")
    kb.button(text="❌ Bekor qilish", callback_data="flow:cancel")
    kb.adjust(1)
    return kb.as_markup()


def channels_list_kb(channels: Iterable[dict[str, Any]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for channel in channels:
        kb.button(
            text=f"🗑 {_short(channel['title'])}",
            callback_data=f"ch:del:{channel['chat_id']}",
        )
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ch:list"))
    kb.row(InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="menu:main"))
    return kb.as_markup()


def channel_delete_confirm_kb(chat_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Ha, o'chirilsin", callback_data=f"ch:delyes:{chat_id}")
    kb.button(text="⬅️ Yo'q", callback_data="ch:list")
    kb.adjust(1)
    return kb.as_markup()


def admins_list_kb(admins: Iterable[dict[str, Any]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for admin in admins:
        name = admin["full_name"] or str(admin["user_id"])
        kb.button(text=f"🗑 {_short(name)}", callback_data=f"adm:del:{admin['user_id']}")
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="adm:add"))
    kb.row(InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="menu:main"))
    return kb.as_markup()
