"""Baza qatlami: lokalda SQLite, Render'da Postgres.

`DATABASE_URL` berilgan bo'lsa Postgres, aks holda SQLite fayli ishlatiladi.
Ikkala backend ham bir xil API beradi — `execute` / `fetchone` / `fetchall`.

So'rovlar hamma joyda `?` bilan yoziladi; Postgres backend ularni o'zi
`$1, $2, …` ga o'giradi. Shu tufayli `channels.py` va `admins.py` da backendga
bog'liq hech narsa yo'q.
"""

import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiosqlite

from config import DATABASE_URL, DB_PATH, USE_POSTGRES

log = logging.getLogger(__name__)

_db: "Database | None" = None

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    chat_id    INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL DEFAULT '',
    username   TEXT,
    type       TEXT    NOT NULL DEFAULT 'channel',
    is_active  INTEGER NOT NULL DEFAULT 1,
    added_by   INTEGER,
    added_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admins (
    user_id    INTEGER PRIMARY KEY,
    full_name  TEXT    NOT NULL DEFAULT '',
    username   TEXT,
    added_by   INTEGER,
    added_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# chat_id manfiy va katta bo'ladi (-1003206905432) — BIGINT shart.
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    chat_id    BIGINT PRIMARY KEY,
    title      TEXT        NOT NULL DEFAULT '',
    username   TEXT,
    type       TEXT        NOT NULL DEFAULT 'channel',
    is_active  INTEGER     NOT NULL DEFAULT 1,
    added_by   BIGINT,
    added_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admins (
    user_id    BIGINT PRIMARY KEY,
    full_name  TEXT        NOT NULL DEFAULT '',
    username   TEXT,
    added_by   BIGINT,
    added_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class Database:
    """Backendlar uchun umumiy interfeys."""

    async def execute(self, sql: str, *args: Any) -> None:
        raise NotImplementedError

    async def fetchone(self, sql: str, *args: Any) -> dict[str, Any] | None:
        raise NotImplementedError

    async def fetchall(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class SQLiteDatabase(Database):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @classmethod
    async def create(cls, path: str) -> "SQLiteDatabase":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.executescript(SQLITE_SCHEMA)
        await conn.commit()
        log.info("Baza: SQLite (%s)", path)
        return cls(conn)

    async def execute(self, sql: str, *args: Any) -> None:
        await self._conn.execute(sql, args)
        await self._conn.commit()

    async def fetchone(self, sql: str, *args: Any) -> dict[str, Any] | None:
        cursor = await self._conn.execute(sql, args)
        row = await cursor.fetchone()
        return dict(row) if row is not None else None

    async def fetchall(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(sql, args)
        return [dict(row) for row in await cursor.fetchall()]

    async def close(self) -> None:
        await self._conn.close()


_PLACEHOLDER = re.compile(r"\?")

# asyncpg libpq ning ba'zi parametrlarini tushunmaydi; Neon ularni o'zi qo'shadi.
_UNSUPPORTED_DSN_PARAMS = {"channel_binding"}


def normalize_dsn(dsn: str) -> str:
    """Neon/Render URL ini asyncpg tushunadigan ko'rinishga keltiradi."""
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://"):]
    parts = urlsplit(dsn)
    query = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _UNSUPPORTED_DSN_PARAMS
    ]
    return urlunsplit(parts._replace(query=urlencode(query)))


class PostgresDatabase(Database):
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, dsn: str) -> "PostgresDatabase":
        import asyncpg  # faqat Postgres rejimida kerak

        pool = await asyncpg.create_pool(
            normalize_dsn(dsn), min_size=1, max_size=5, command_timeout=30
        )
        async with pool.acquire() as conn:
            await conn.execute(POSTGRES_SCHEMA)
        log.info("Baza: PostgreSQL")
        return cls(pool)

    @staticmethod
    def _convert(sql: str) -> str:
        """`?` -> `$1, $2, …`"""
        counter = 0

        def replace(_: re.Match[str]) -> str:
            nonlocal counter
            counter += 1
            return f"${counter}"

        return _PLACEHOLDER.sub(replace, sql)

    async def execute(self, sql: str, *args: Any) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(self._convert(sql), *args)

    async def fetchone(self, sql: str, *args: Any) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(self._convert(sql), *args)
        return dict(row) if row is not None else None

    async def fetchall(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(self._convert(sql), *args)
        return [dict(row) for row in rows]

    async def close(self) -> None:
        await self._pool.close()


async def init_db() -> Database:
    global _db
    if USE_POSTGRES:
        _db = await PostgresDatabase.create(DATABASE_URL)
    else:
        _db = await SQLiteDatabase.create(DB_PATH)
    return _db


def db() -> Database:
    if _db is None:
        raise RuntimeError("Baza ishga tushirilmagan — avval init_db() chaqiring")
    return _db


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
