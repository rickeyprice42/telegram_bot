import sqlite3
import json
from pathlib import Path

DB_PATH = Path("database/bot.db")
CATALOG_JSON_PATH = Path("data/ai_tools.json")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seed_catalog_from_json(cursor):
    if not CATALOG_JSON_PATH.exists():
        return

    with CATALOG_JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    categories = data.get("categories", {})
    for category_index, (category_key, category_data) in enumerate(categories.items()):
        cursor.execute(
            """
            INSERT OR IGNORE INTO categories (category_key, title, sort_order)
            VALUES (?, ?, ?)
            """,
            (
                category_key,
                category_data["title"],
                category_index,
            ),
        )

        for tool_index, tool in enumerate(category_data.get("tools", [])):
            cursor.execute(
                """
                INSERT OR IGNORE INTO tools (
                    tool_id,
                    category_key,
                    name,
                    description,
                    link,
                    image,
                    sort_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool["id"],
                    category_key,
                    tool["name"],
                    tool["description"],
                    tool["link"],
                    tool.get("image"),
                    tool_index,
                ),
            )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tool_id TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_key TEXT UNIQUE,
        title TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_id TEXT UNIQUE,
        category_key TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        link TEXT NOT NULL,
        image TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (category_key) REFERENCES categories(category_key)
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM categories")
    categories_count = cursor.fetchone()[0]
    if categories_count == 0:
        seed_catalog_from_json(cursor)

    conn.commit()
    conn.close()
