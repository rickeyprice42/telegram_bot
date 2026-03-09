import json


def load_catalog():
    with open("data/ai_tools.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_categories():
    data = load_catalog()
    return data["categories"]