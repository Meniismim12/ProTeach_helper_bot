"""Kanallar bilan ishlash."""

from typing import Any

from .db import db


async def upsert_channel(
    chat_id: int,
    title: str,
    username: str | None,
    chat_type: str,
    added_by: int | None,
) -> bool:
    """Kanalni saqlaydi. Yangi qo'shilgan bo'lsa True qaytaradi."""
    existing = await db().fetchone(
        "SELECT 1 AS found FROM channels WHERE chat_id = ?", chat_id
    )
    await db().execute(
        """
        INSERT INTO channels (chat_id, title, username, type, is_active, added_by)
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT (chat_id) DO UPDATE SET
            title     = excluded.title,
            username  = excluded.username,
            type      = excluded.type,
            is_active = 1
        """,
        chat_id,
        title,
        username,
        chat_type,
        added_by,
    )
    return existing is None


async def deactivate_channel(chat_id: int) -> None:
    await db().execute("UPDATE channels SET is_active = 0 WHERE chat_id = ?", chat_id)


async def delete_channel(chat_id: int) -> None:
    await db().execute("DELETE FROM channels WHERE chat_id = ?", chat_id)


async def update_title(chat_id: int, title: str, username: str | None) -> None:
    await db().execute(
        "UPDATE channels SET title = ?, username = ? WHERE chat_id = ?",
        title,
        username,
        chat_id,
    )


async def get_active_channels() -> list[dict[str, Any]]:
    return await db().fetchall(
        "SELECT * FROM channels WHERE is_active = 1 ORDER BY lower(title)"
    )


async def get_all_channels() -> list[dict[str, Any]]:
    return await db().fetchall(
        "SELECT * FROM channels ORDER BY is_active DESC, lower(title)"
    )


async def get_channel(chat_id: int) -> dict[str, Any] | None:
    return await db().fetchone("SELECT * FROM channels WHERE chat_id = ?", chat_id)
