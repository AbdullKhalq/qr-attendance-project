"""Application configuration and local-network address discovery."""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PORT = 5000


def _is_usable_ipv4(value: str) -> bool:
    """Return True for a non-loopback IPv4 address usable by another device."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return (
        address.version == 4
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_unspecified
    )


def discover_host_ipv4() -> str:
    """Discover the IPv4 address used by the host's active network route.

    Opening a UDP socket this way does not send application data. It asks the
    operating system which local interface it would use for an external route.
    Hostname resolution is used as a secondary method for offline networks.
    """
    candidates: list[str] = []

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("8.8.8.8", 80))
            candidates.append(connection.getsockname()[0])
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        for result in socket.getaddrinfo(
            hostname,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
        ):
            candidates.append(result[4][0])
    except OSError:
        pass

    # Prefer normal private LAN addresses over VPN/public interfaces.
    usable = [candidate for candidate in dict.fromkeys(candidates) if _is_usable_ipv4(candidate)]
    for candidate in usable:
        if ipaddress.ip_address(candidate).is_private:
            return candidate
    if usable:
        return usable[0]

    # This fallback keeps desktop-only use working when no network is active.
    return "127.0.0.1"


def default_public_base_url(port: int = DEFAULT_PORT) -> str:
    """Build the URL embedded in generated attendance QR codes."""
    return f"http://{discover_host_ipv4()}:{port}"


@dataclass(frozen=True)
class ProjectConfig:
    base_dir: Path
    data_dir: Path
    blockchain_file: Path
    students_file: Path
    qr_tokens_file: Path
    secret_key: str
    public_base_url: str

    @classmethod
    def from_environment(cls, base_dir: Path | None = None) -> "ProjectConfig":
        root = (base_dir or Path(__file__).resolve().parent).resolve()
        data_dir = Path(os.getenv("ATTENDANCE_DATA_DIR", root / "data")).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)

        configured_url = os.getenv("PUBLIC_BASE_URL", "").strip()
        public_base_url = configured_url or default_public_base_url()

        return cls(
            base_dir=root,
            data_dir=data_dir,
            blockchain_file=data_dir / "attendance_chain.json",
            students_file=data_dir / "students.json",
            qr_tokens_file=data_dir / "qr_tokens.json",
            secret_key=os.getenv("ATTENDANCE_SECRET_KEY", "change-this-demo-secret"),
            public_base_url=public_base_url,
        )
