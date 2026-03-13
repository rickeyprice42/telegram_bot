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

def add_tool(tool_id, category_key, name, description, link, image=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tools (
            tool_id,
            category_key,
            name,
            description,
            link,
            image
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        tool_id,
        category_key,
        name,
        description,
        link,
        image
    ))

    conn.commit()
    conn.close()


def delete_tool(tool_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM tools WHERE tool_id = ?",
        (tool_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute(
        "DELETE FROM favorites WHERE tool_id = ?",
        (tool_id,)
    )
    cursor.execute(
        "DELETE FROM tools WHERE tool_id = ?",
        (tool_id,)
    )

    conn.commit()
    conn.close()
    return row["name"]

def get_top_tools_by_category(category_key):
    query = """
    SELECT 
        t.tool_id,
        t.name,
        COUNT(f.tool_id) AS favorites_count,
        COALESCE(r.rating, 0) AS external_rating,
        (COUNT(f.tool_id) * 2 + COALESCE(r.rating, 0)) AS score
    FROM tools t
    LEFT JOIN favorites f ON t.tool_id = f.tool_id
    LEFT JOIN tool_ratings r ON t.tool_id = r.tool_id
    WHERE t.category_key = ?
    GROUP BY t.tool_id
    ORDER BY score DESC
    LIMIT 3
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (category_key,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_categories():
    query = "SELECT category_key, title FROM categories ORDER BY sort_order"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_tools():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tool_id, category_key, name
        FROM tools
        ORDER BY category_key, sort_order, name
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_tool_rating(tool_id, rating):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tool_ratings (tool_id, rating, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(tool_id) DO UPDATE SET
            rating = excluded.rating,
            updated_at = CURRENT_TIMESTAMP
        """,
        (tool_id, rating),
    )
    conn.commit()
    conn.close()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        banned INTEGER DEFAULT 0,
        date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("PRAGMA table_info(users)")
    user_columns = {row["name"] for row in cursor.fetchall()}
    if "banned" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tool_ratings (
        tool_id TEXT PRIMARY KEY,
        rating REAL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS use_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_key TEXT UNIQUE,
    title TEXT,
    emoji TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tool_use_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id TEXT,
    case_key TEXT
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM use_cases")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
        "INSERT INTO use_cases (case_key, title, emoji) VALUES (?, ?, ?)",
        [
            ("text", "Написать текст", "📝"),
            ("image", "Создать изображение", "🎨"),
            ("video", "Создать видео", "🎬"),
            ("code", "Написать код", "💻"),
            ("data", "Анализировать данные", "📊"),
        ]
    )

    cursor.execute("SELECT COUNT(*) FROM categories")
    categories_count = cursor.fetchone()[0]
    if categories_count == 0:
        seed_catalog_from_json(cursor)

    conn.commit()
    conn.close()
