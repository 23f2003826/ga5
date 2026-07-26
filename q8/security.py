from pathlib import Path
from urllib.parse import urlparse
import ipaddress
import socket

SANDBOX = Path("/srv/agent-redteam/sandbox-0de282cacd").resolve()

ALLOWED_HOSTS = {
    "example.com",
    "www.iana.org",
}


def validate_path(user_path: str):
    if not isinstance(user_path, str) or not user_path:
        return False, "invalid path"

    try:
        target = (SANDBOX / user_path).resolve(strict=False)
    except Exception:
        return False, "invalid path"

    try:
        target.relative_to(SANDBOX)
    except ValueError:
        return False, "path traversal"

    if not target.exists():
        return False, "file not found"

    if not target.is_file():
        return False, "not a file"

    return True, target


def validate_url(url: str):
    if not isinstance(url, str) or not url:
        return False, "invalid url"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "invalid url"

    if parsed.scheme not in ("http", "https"):
        return False, "invalid scheme"

    if parsed.username or parsed.password:
        return False, "userinfo not allowed"

    host = parsed.hostname

    if host is None:
        return False, "invalid host"

    host = host.lower().rstrip(".")

    if host not in ALLOWED_HOSTS:
        return False, "host not allowed"

    try:
        infos = socket.getaddrinfo(host, None)

        for info in infos:
            ip = ipaddress.ip_address(info[4][0])

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False, "private address"
    except Exception:
        return False, "dns failed"

    return True, url