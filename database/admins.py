"""Adminlar bilan ishlash. OWNER_ID doim admin hisoblanadi."""

from typing import Any

from config import OWNER_ID

from .db import db


async def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    row = await db().fetchone("SELECT 1 AS found FROM admins WHERE user_id = ?", user_id)
    return row is not None


async def add_admin(
    user_id: int,
    full_name: str,
    username: str | None,
    added_by: int,
) -> None:
    await db().execute(
        """
        INSERT INTO admins (user_id, full_name, username, added_by)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            full_name = excluded.full_name,
            username  = excluded.username
        """,
        user_id,
        full_name,
        username,
        added_by,
    )


async def remove_admin(user_id: int) -> None:
    await db().execute("DELETE FROM admins WHERE user_id = ?", user_id)


async def get_admins() -> list[dict[str, Any]]:
    return await db().fetchall("SELECT * FROM admins ORDER BY added_at")
