"""Sozlamalar .env fayldan yoki hosting env o'zgaruvchilaridan o'qiladi."""

import hashlib
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID: int = int(os.getenv("OWNER_ID", "0") or 0)

# --------------------------------------------------------------------------- #
# Baza
# --------------------------------------------------------------------------- #
# DATABASE_URL berilgan bo'lsa — Postgres (Render/Neon), aks holda SQLite fayl.
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")
USE_POSTGRES: bool = bool(DATABASE_URL)

# --------------------------------------------------------------------------- #
# Ishlash rejimi: webhook (Render) yoki polling (lokal / VPS)
# --------------------------------------------------------------------------- #
# Render RENDER_EXTERNAL_URL ni o'zi beradi — qo'lda hech narsa yozish shart emas.
WEBHOOK_BASE_URL: str = (
    os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
).strip().rstrip("/")
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
PORT: int = int(os.getenv("PORT", "8080") or 8080)
USE_WEBHOOK: bool = bool(WEBHOOK_BASE_URL)

# Telegram har bir so'rovga shu maxfiy kalitni qo'shib yuboradi — begona
# so'rovlar shu orqali rad etiladi. Berilmasa tokendan hosil qilinadi.
WEBHOOK_SECRET: str = (
    os.getenv("WEBHOOK_SECRET", "").strip()
    or hashlib.sha256(BOT_TOKEN.encode()).hexdigest()[:32]
)

# --------------------------------------------------------------------------- #
# Yuborish
# --------------------------------------------------------------------------- #
# Kanallar orasidagi pauza. Telegram sekundiga ~30 xabarga ruxsat beradi.
SEND_DELAY: float = float(os.getenv("SEND_DELAY", "0.06"))

# Albom (media group) qismlarini yig'ish uchun kutish vaqti.
ALBUM_LATENCY: float = float(os.getenv("ALBUM_LATENCY", "0.7"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN ko'rsatilmagan")
if not OWNER_ID:
    raise RuntimeError("OWNER_ID ko'rsatilmagan")
