from database.database import get_connection


def add_user(user_id, username, first_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (user_id, username, first_name))

    is_new_user = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return is_new_user

def create_favorites_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tool_id TEXT
        )
    """)

    conn.commit()
    conn.close()

def add_favorite(user_id, tool_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO favorites (user_id, tool_id) VALUES (?, ?)",
        (user_id, tool_id)
    )

    conn.commit()
    conn.close()

def is_favorite(user_id, tool_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM favorites WHERE user_id=? AND tool_id=?",
        (user_id, tool_id)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None

def remove_favorite(user_id, tool_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM favorites WHERE user_id=? AND tool_id=?",
        (user_id, tool_id)
    )

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted

def get_user_favorites(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT tool_id FROM favorites WHERE user_id=?",
        (user_id,)
    )

    tools = cursor.fetchall()

    conn.close()

    return [tool[0] for tool in tools]

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return user


def set_user_ban_status(user_id, banned):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET banned = ? WHERE user_id = ?",
        (1 if banned else 0, user_id),
    )

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def ban_user(user_id):
    return set_user_ban_status(user_id, True)


def unban_user(user_id):
    return set_user_ban_status(user_id, False)


def is_user_banned(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT banned FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    return bool(row["banned"]) if row else False

def get_users_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users")

    users = cursor.fetchall()

    conn.close()

    return users
