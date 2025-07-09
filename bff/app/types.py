import enum
from collections.abc import Callable


class Config:
    app_name: str = "BFF"
    version: str = "1.0.0"
    server_port: int = 0xBFF
    repository: str|None = None
    docu_depot: str|None = None


class DefaultViews(enum.Enum):
    _404 = "(˚Δ˚)b"
    HOME = enum.auto()
    SETTINGS = enum.auto()
    USERS = enum.auto()
    ABOUT = enum.auto()
