from dataclasses import dataclass


@dataclass
class DeviceActionRequest:
    action: str


@dataclass
class DeviceInfo:
    host: str
    os: str
    release: str
    python_version: str
    uptime: str
    timestamp: str
    network: dict
    battery: dict
