from pathlib import Path
import requests

SANDBOX = Path("/srv/agent-redteam/sandbox-0de282cacd")

def read_file(path: str):

    resolved = (SANDBOX / path).resolve()

    return resolved.read_text()


def fetch_url(url):

    r = requests.get(
        url,
        timeout=5,
        allow_redirects=False,
    )

    return r.text