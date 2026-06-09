from dataclasses import dataclass


@dataclass
class SystemStatus:
    host: str
    os: str
    release: str
    python_version: str
    uptime: str
    timestamp: str
