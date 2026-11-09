from framework.config import get


def run() -> str:
    return get("app.message")
