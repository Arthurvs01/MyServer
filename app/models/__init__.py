from pydantic import BaseModel


class SystemStatus(BaseModel):
    host: str
    os: str
    release: str
    python_version: str
    uptime: str
    timestamp: str
