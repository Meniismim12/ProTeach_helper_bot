"""E'lon yaratish va kanallarga tarqatish."""

import html
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database.channels import get_active_channels
from keyboards.inline import (
    ask_buttons_kb,
    cancel_kb,
    channels_menu_kb,
    channels_select_kb,
    confirm_kb,
    main_menu,
    skip_text_kb,
)
from utils.buttons import build_markup, parse_buttons
from utils.post import broadcast, build_payload, deliver
from utils.ui import edit_screen, safe_edit

router = Router(name="post")
log = logging.getLogger(__name__)

MAX_LISTED = 30


class PostSG(StatesGroup):
    content = State()
    ask_buttons = State()
    buttons = State()
    album_text = State()
    channels = State()
    confirm = State()


ASK_CONTENT = (
    "📝 <b>E'lonni yuboring</b>\n\n"
    "Matn, rasm, video, fayl, ovozli xabar, stiker yoki albom (bir nechta rasm/video) — "
    "botga nima yuborsangiz, kanalga aynan o'shanday ketadi.\n\n"
    "Formatlash (qalin, kursiv, havola) saqlanadi."
)

ASK_BUTTONS = (
    "🔗 <b>Tugmalarni yuboring</b>\n\n"
    "Har bir qator — alohida tugmalar qatori.\n"
    "Bitta qatorga bir nechta tugma qo'yish uchun <code>|</code> ishlating.\n\n"
    "<b>Namuna:</b>\n"
    "<code>📚 Kursga yozilish - https://t.me/misol\n"
    "🌐 Sayt - https://misol.uz | 📸 Instagram - @misol</code>"
)

def _menu_text(selected: int, total: int) -> str:
    """Kanal bosqichining bosh ekrani."""
    return (
        "📡 <b>Qaysi kanallarga yuborilsin?</b>\n\n"
        f"Tanlangan: <b>{selected}</b> / {total} ta\n\n"
        "☑️ <b>Hammasi</b> — barcha kanallarga yuboriladi\n"
        "📡 <b>Kanallar tanlash</b> — ro'yxatdan o'zingiz belgilaysiz\n"
        "👀 <b>Ko'rib chiqish</b> — yuborishdan oldin ko'rasiz"
    )


def _list_text(selected: int, total: int) -> str:
    """Kanallar ro'yxati ekrani."""
    return (
        "📋 <b>Kanallar ro'yxati</b>\n\n"
        "Kerakli kanal ustiga bosing — u ✅ bo'lib qoladi.\n"
        "Yana bir marta bossangiz belgi olinadi va o'sha kanalga e'lon bormaydi.\n\n"
        f"Tanlangan: <b>{selected}</b> / {total} ta\n\n"
        "Tanlab bo'lgach «✔️ Tayyor» tugmasini bosing."
    )


# --------------------------------------------------------------------------- #
# 1-bosqich: e'lon mazmuni
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "post:new")
async def new_post(call: CallbackQuery, state: FSMContext) -> None:
    channels = await get_active_channels()
    if not channels:
        await call.answer(
            "Avval botni kanalga qo'shib, admin qiling!", show_alert=True
        )
        return

    await state.clear()
    await state.set_state(PostSG.content)
    await safe_edit(call, ASK_CONTENT, cancel_kb())
    await call.answer()


@router.message(PostSG.content)
async def got_content(
    message: Message,
    state: FSMContext,
    album: list[Message] | None = None,
) -> None:
    payload = build_payload(message, album)
    if payload is None:
        await message.answer(
            "❌ Bu albomni qayta yuborib bo'lmadi. Boshqa xabar yuboring yoki /cancel."
        )
        return

    await state.update_data(post=payload)
    await state.set_state(PostSG.ask_buttons)

    info = (
        f"🖼 Albom qabul qilindi ({len(payload['media'])} ta fayl)"
        if payload["kind"] == "album"
        else "✅ E'lon qabul qilindi"
    )
    await message.answer(
        f"{info}\n\nE'lon ostiga havolali tugma qo'shasizmi?",
        reply_markup=ask_buttons_kb(),
    )


# --------------------------------------------------------------------------- #
# 2-bosqich: tugmalar
# --------------------------------------------------------------------------- #
@router.callback_query(PostSG.ask_buttons, F.data == "post:btn:yes")
async def want_buttons(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PostSG.buttons)
    await safe_edit(call, ASK_BUTTONS, cancel_kb())
    await call.answer()


@router.callback_query(PostSG.ask_buttons, F.data == "post:btn:no")
async def no_buttons(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _show_channels(call.message, state)


@router.message(PostSG.buttons, F.text)
async def got_buttons(message: Message, state: FSMContext) -> None:
    try:
        parse_buttons(message.text)
    except ValueError as exc:
        await message.answer(f"❌ {exc}\n\nQaytadan yuboring yoki /cancel.")
        return

    await state.update_data(buttons_raw=message.text)
    data = await state.get_data()

    if data["post"]["kind"] == "album":
        await state.set_state(PostSG.album_text)
        await message.answer(
            "⚠️ Telegram albom <b>ostiga</b> tugma qo'yishga ruxsat bermaydi.\n"
            "Shuning uchun tugmalar albomdan keyin alohida xabarda ketadi.\n\n"
            "O'sha xabar matnini yuboring "
            "(masalan: <i>Batafsil ma'lumot uchun 👇</i>):",
            reply_markup=skip_text_kb(),
        )
        return

    await _show_channels(message, state)


@router.message(PostSG.buttons)
async def buttons_not_text(message: Message) -> None:
    await message.answer("❌ Tugmalarni <b>matn</b> ko'rinishida yuboring yoki /cancel.")


@router.message(PostSG.album_text, F.text)
async def got_album_text(message: Message, state: FSMContext) -> None:
    await state.update_data(album_text=message.html_text)
    await _show_channels(message, state)


@router.message(PostSG.album_text)
async def album_text_not_text(message: Message) -> None:
    await message.answer(
        "❌ Bu yerda faqat <b>matn</b> kutilmoqda — tugmalar bilan birga ketadigan "
        "xabar matnini yozing, «⏭ Matnsiz» tugmasini bosing yoki /cancel."
    )


@router.callback_query(PostSG.album_text, F.data == "post:skip_text")
async def skip_album_text(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(album_text="👇")
    await call.answer()
    await _show_channels(call.message, state)


# --------------------------------------------------------------------------- #
# 3-bosqich: kanallarni tanlash
# --------------------------------------------------------------------------- #
async def _show_channels(target: Message, state: FSMContext) -> None:
    """Kanal bosqichini boshlaydi. Dastlab hech biri tanlanmagan."""
    rows = await get_active_channels()
    channels = [dict(row) for row in rows]
    if not channels:
        await state.clear()
        await target.answer("❌ Faol kanal qolmadi. Avval botni kanalga admin qiling.")
        return

    await state.update_data(all_channels=channels, selected=[])
    await state.set_state(PostSG.channels)
    await target.answer(_menu_text(0, len(channels)), reply_markup=channels_menu_kb())


@router.callback_query(PostSG.channels, F.data.startswith("sel:"))
async def select_channels(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Kanal bosqichining barcha tugmalari.

    Barcha ekran almashishlari xabarni JOYIDA tahrirlaydi — chatga yangi
    xabar qo'shilmaydi.
    """
    action = call.data.removeprefix("sel:")
    data = await state.get_data()
    channels: list[dict] = data["all_channels"]
    selected: set[int] = set(data["selected"])
    total = len(channels)

    # «👀 Ko'rib chiqish» — preview ekraniga o'tish
    if action == "done":
        if not selected:
            await call.answer(
                "Avval kamida bitta kanal tanlang!\n\n"
                "«📡 Kanallar tanlash» yoki «☑️ Hammasi» tugmasidan foydalaning.",
                show_alert=True,
            )
            return
        await call.answer()
        await _preview(call.message, state, bot)
        return

    # «📡 Kanallar tanlash» — ro'yxatni ochish
    if action == "open":
        await call.answer()
        await edit_screen(
            call, _list_text(len(selected), total), channels_select_kb(channels, selected)
        )
        return

    # «✔️ Tayyor» — ro'yxatdan bosh menyuga qaytish
    if action == "back":
        await call.answer(f"Tanlandi: {len(selected)} ta")
        await edit_screen(call, _menu_text(len(selected), total), channels_menu_kb())
        return

    # «☑️ Hammasi»
    if action == "all":
        selected = {channel["chat_id"] for channel in channels}
        await state.update_data(selected=list(selected))
        await call.answer(f"Hammasi tanlandi: {total} ta")
        await edit_screen(call, _menu_text(len(selected), total), channels_menu_kb())
        return

    # Kanal ustiga bosildi — belgini almashtiramiz
    if action.startswith("t:"):
        chat_id = int(action.removeprefix("t:"))
        title = next(
            (c["title"] for c in channels if c["chat_id"] == chat_id), "Kanal"
        )
        if chat_id in selected:
            selected.discard(chat_id)
            note = f"⬜️ {title} — bekor qilindi"
        else:
            selected.add(chat_id)
            note = f"✅ {title} — tanlandi"

        await state.update_data(selected=list(selected))
        await call.answer(note)
        await edit_screen(
            call, _list_text(len(selected), total), channels_select_kb(channels, selected)
        )
        return

    await call.answer()


@router.callback_query(PostSG.confirm, F.data == "post:back")
async def back_to_channels(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    channels: list[dict] = data["all_channels"]
    selected = set(data["selected"])
    await state.set_state(PostSG.channels)
    await call.answer()
    await edit_screen(call, _menu_text(len(selected), len(channels)), channels_menu_kb())


# --------------------------------------------------------------------------- #
# 4-bosqich: ko'rib chiqish va yuborish
# --------------------------------------------------------------------------- #
async def _preview(target: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    post = data["post"]
    markup = build_markup(data.get("buttons_raw"))
    album_text = data.get("album_text")
    selected = set(data["selected"])
    channels = [c for c in data["all_channels"] if c["chat_id"] in selected]

    await state.set_state(PostSG.confirm)
    await target.answer("👀 <b>E'lon kanalda quyidagicha ko'rinadi:</b>")
    await deliver(bot, target.chat.id, post, markup, album_text)

    names = [
        f"• {html.escape(c['title'] or 'Nomsiz')}" for c in channels[:MAX_LISTED]
    ]
    if len(channels) > MAX_LISTED:
        names.append(f"• …va yana {len(channels) - MAX_LISTED} ta")

    await target.answer(
        f"📡 <b>Tanlangan kanallar ({len(channels)} ta):</b>\n"
        + "\n".join(names)
        + "\n\nYuborilsinmi?",
        reply_markup=confirm_kb(),
    )


@router.callback_query(PostSG.confirm, F.data == "post:send")
async def do_send(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    post = data["post"]
    markup = build_markup(data.get("buttons_raw"))
    album_text = data.get("album_text")
    selected = set(data["selected"])
    channels = [c for c in data["all_channels"] if c["chat_id"] in selected]

    await call.answer()
    await safe_edit(call, f"📤 Yuborilmoqda… ({len(channels)} ta kanal)")

    sent, failed = await broadcast(bot, post, markup, channels, album_text)
    await state.clear()

    lines = [
        "✅ <b>E'lon yuborildi</b>\n",
        f"📤 Muvaffaqiyatli: <b>{len(sent)}</b> ta",
    ]
    if failed:
        lines.append(f"❌ Xatolik: <b>{len(failed)}</b> ta\n")
        lines.append("<b>Xatoliklar:</b>")
        for channel, reason in failed[:15]:
            title = html.escape(channel["title"] or "Nomsiz")
            lines.append(f"• {title} — {html.escape(reason)[:100]}")
        if len(failed) > 15:
            lines.append(f"• …va yana {len(failed) - 15} ta")

    await call.message.answer(
        "\n".join(lines),
        reply_markup=main_menu(is_owner=call.from_user.id == OWNER_ID),
    )
    log.info("E'lon yuborildi: %s ok, %s xato", len(sent), len(failed))
