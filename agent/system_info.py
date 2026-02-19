import platform
import socket
import getpass
from datetime import datetime, timezone


def _get_ip_address() -> str:
    """
    Returns the local IP address without making external network calls.
    Falls back safely if resolution fails.
    """
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return "UNKNOWN"


def collect_system_info() -> dict:
    """
    Collects basic system metadata.
    This function is pure: no IO, no logging, no prints.
    """
    return {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "ip_address": _get_ip_address(),
        "timestamp": datetime.now().isoformat() + "Z",
    }
