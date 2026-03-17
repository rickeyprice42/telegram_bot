from database.database import get_connection


def load_catalog():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT category_key, title
        FROM categories
        ORDER BY sort_order, id
        """
    )
    categories_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT t.tool_id, tc.category_key, t.name, t.description, t.link, t.image
        FROM tools t
        JOIN tool_categories tc ON t.tool_id = tc.tool_id
        ORDER BY tc.category_key, t.sort_order, t.id
        """
    )
    tools_rows = cursor.fetchall()
    conn.close()

    categories = {
        row["category_key"]: {
            "title": row["title"],
            "tools": [],
        }
        for row in categories_rows
    }

    for row in tools_rows:
        category = categories.get(row["category_key"])
        if not category:
            continue

        category["tools"].append(
            {
                "id": row["tool_id"],
                "name": row["name"],
                "description": row["description"],
                "link": row["link"],
                "image": row["image"],
            }
        )

    return {"categories": categories}


def get_categories():
    data = load_catalog()
    return data["categories"]
