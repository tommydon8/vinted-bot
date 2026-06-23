import sqlite3
from pathlib import Path

DB_PATH = Path("data/bot.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                username  TEXT,
                first_name TEXT
            );
            CREATE TABLE IF NOT EXISTS brands (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                brand_name      TEXT NOT NULL,
                vinted_brand_id INTEGER NOT NULL,
                UNIQUE(user_id, brand_name),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS seen_items (
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, item_id)
            );
        """)


def upsert_user(user_id: int, username: str, first_name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username or "", first_name or ""),
        )


def get_user_brands(user_id: int) -> list[tuple[str, int]]:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT brand_name, vinted_brand_id FROM brands WHERE user_id = ? ORDER BY brand_name",
            (user_id,),
        ).fetchall()


def add_brand(user_id: int, brand_name: str, vinted_brand_id: int) -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO brands (user_id, brand_name, vinted_brand_id) VALUES (?, ?, ?)",
                (user_id, brand_name, vinted_brand_id),
            )
        return True
    except sqlite3.IntegrityError:
        return False  # already exists


def remove_brand_by_name(user_id: int, brand_name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM brands WHERE user_id = ? AND brand_name = ?",
            (user_id, brand_name),
        )


def remove_brand(user_id: int, vinted_brand_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM brands WHERE user_id = ? AND vinted_brand_id = ?",
            (user_id, vinted_brand_id),
        )


def get_all_active_user_ids() -> list[int]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT DISTINCT user_id FROM brands").fetchall()
        return [r[0] for r in rows]


def is_seen(user_id: int, item_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT 1 FROM seen_items WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone() is not None


def mark_seen(user_id: int, item_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_items (user_id, item_id) VALUES (?, ?)",
            (user_id, item_id),
        )


def reset_seen(user_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM seen_items WHERE user_id = ?", (user_id,))
