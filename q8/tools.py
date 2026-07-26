from pathlib import Path
import requests


def read_file(path: Path):
    return path.read_text(encoding="utf-8")


def fetch_url(url: str):
    response = requests.get(
        url,
        timeout=5,
        allow_redirects=False,
    )

    return response.text