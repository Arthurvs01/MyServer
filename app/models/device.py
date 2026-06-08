from pydantic import BaseModel


class DeviceActionRequest(BaseModel):
    action: str


class DeviceInfo(BaseModel):
    host: str
    os: str
    release: str
    python_version: str
    uptime: str
    timestamp: str
    network: dict
    battery: dict
