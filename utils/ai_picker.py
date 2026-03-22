from database.database import get_connection


LEVEL_TAGS = {
    "easy": "Легкая",
    "medium": "Средняя",
    "hard": "Сложная",
}

PREFERENCE_TAGS = {
    "free": "Бесплатная",
    "fast": "Быстрая",
    "quality": "Максимальное качество",
}


def get_use_cases():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT case_key, title, emoji FROM use_cases ORDER BY id")
    cases = cursor.fetchall()

    conn.close()
    return cases


def get_use_case_by_key(case_key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT case_key, title, emoji
        FROM use_cases
        WHERE case_key = ?
        """,
        (case_key,),
    )
    row = cursor.fetchone()

    conn.close()
    return row


def get_tools_for_case(case_key, level_tag=None, preference_tag=None):
    score_parts = []

    if level_tag == "easy":
        score_parts.append("CASE WHEN COALESCE(tools.tag_easy, 0) = 1 THEN 2 ELSE 0 END")
    elif level_tag == "medium":
        score_parts.append("CASE WHEN COALESCE(tools.tag_medium, 0) = 1 THEN 2 ELSE 0 END")
    elif level_tag == "hard":
        score_parts.append("CASE WHEN COALESCE(tools.tag_hard, 0) = 1 THEN 2 ELSE 0 END")

    if preference_tag == "free":
        score_parts.append("CASE WHEN COALESCE(tools.tag_free, 0) = 1 THEN 1 ELSE 0 END")
    elif preference_tag == "fast":
        score_parts.append("CASE WHEN COALESCE(tools.tag_fast, 0) = 1 THEN 1 ELSE 0 END")
    elif preference_tag == "quality":
        score_parts.append("CASE WHEN COALESCE(tools.tag_quality, 0) = 1 THEN 1 ELSE 0 END")

    match_score_sql = " + ".join(score_parts) if score_parts else "0"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT
            tools.name,
            tools.description,
            tools.link,
            COALESCE(tool_ratings.rating, 0) AS rating,
            ({match_score_sql}) AS match_score
        FROM tools
        JOIN tool_use_cases
            ON tools.tool_id = tool_use_cases.tool_id
        LEFT JOIN tool_ratings
            ON tools.tool_id = tool_ratings.tool_id
        WHERE tool_use_cases.case_key = ?
        ORDER BY match_score DESC, rating DESC, tools.name
        """,
        (case_key,),
    )

    tools = cursor.fetchall()

    conn.close()
    return tools
