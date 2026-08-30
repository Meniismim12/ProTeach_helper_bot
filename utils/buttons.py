"""Admin yozgan matndan inline tugmalar yasash.

Format:
    Har bir qator — tugmalar qatori.
    Bitta qatordagi tugmalar `|` bilan ajratiladi.
    Tugma va havola ` - ` bilan ajratiladi.

Namuna:
    Kursga yozilish - https://t.me/misol
    Sayt - https://misol.uz | Instagram - @misol
"""

import re

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

_SCHEME_RE = re.compile(r"^(https?|tg)://", re.IGNORECASE)


def _normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if url.lower().startswith(("t.me/", "telegram.me/", "www.")):
        return f"https://{url}"
    return url


def parse_buttons(text: str) -> list[list[InlineKeyboardButton]]:
    """Matnni tugmalar jadvaliga aylantiradi. Xato bo'lsa ValueError."""
    rows: list[list[InlineKeyboardButton]] = []

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue

        row: list[InlineKeyboardButton] = []
        for chunk in line.split("|"):
            chunk = chunk.strip()
            if not chunk:
                continue
            if " - " not in chunk:
                raise ValueError(
                    f"«{chunk}» — format noto'g'ri.\n"
                    "Namuna: <code>Tugma matni - https://havola</code>"
                )
            title, url = chunk.rsplit(" - ", 1)
            title = title.strip()
            url = _normalize_url(url)
            if not title:
                raise ValueError("Tugma matni bo'sh bo'lishi mumkin emas.")
            if len(title) > 64:
                raise ValueError(f"«{title[:20]}...» — tugma matni juda uzun (64 belgidan kam bo'lsin).")
            if not _SCHEME_RE.match(url):
                raise ValueError(
                    f"«{url}» — havola noto'g'ri.\n"
                    "U <code>https://</code> yoki <code>@username</code> ko'rinishida bo'lsin."
                )
            row.append(InlineKeyboardButton(text=title, url=url))

        if row:
            rows.append(row)

    if not rows:
        raise ValueError("Hech qanday tugma topilmadi.")
    if len(rows) > 10:
        raise ValueError("Tugmalar qatori 10 tadan oshmasin.")
    return rows


def build_markup(raw: str | None) -> InlineKeyboardMarkup | None:
    """Saqlangan matndan klaviatura yasaydi (xato bo'lsa None)."""
    if not raw:
        return None
    try:
        return InlineKeyboardMarkup(inline_keyboard=parse_buttons(raw))
    except ValueError:
        return None
