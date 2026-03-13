from database.database import get_connection


def get_use_cases():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT case_key, title, emoji FROM use_cases")

    cases = cursor.fetchall()

    conn.close()

    return cases

def get_tools_for_case(case_key):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description, link
        FROM tools
        JOIN tool_use_cases
        ON tools.tool_id = tool_use_cases.tool_id
        WHERE tool_use_cases.case_key = ?
    """, (case_key,))

    tools = cursor.fetchall()

    conn.close()

    return tools