import json


def save_project(data: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
