from datetime import datetime, timezone
import platform


def get_system_info() -> dict:
    return {
        "host": platform.node(),
        "os": platform.system(),
        "release": platform.release(),
        "python_version": platform.python_version(),
        "uptime": get_uptime(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_uptime() -> str:
    try:
        with open("/proc/uptime") as handle:
            seconds = float(handle.readline().split()[0])
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    except FileNotFoundError:
        return "desconhecido"
