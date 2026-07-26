from pathlib import Path
from urllib.parse import urlparse, unquote
import ipaddress
import socket

SANDBOX = Path("/srv/agent-redteam/sandbox-0de282cacd").resolve()

ALLOWED_HOSTS = {
    "example.com",
    "www.iana.org",
}


def validate_path(user_path):

    decoded = unquote(user_path)

    target = (SANDBOX / decoded).resolve()

    try:
        target.relative_to(SANDBOX)
    except ValueError:
        return False, "path traversal"

    return True, target


def validate_url(url):

    p = urlparse(url)

    if p.scheme not in ("http", "https"):
        return False, "invalid scheme"

    if p.username or p.password:
        return False, "userinfo"

    host = p.hostname

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
            ):
                return False, "private ip"

    except Exception:
        return False, "dns"

    return True, host