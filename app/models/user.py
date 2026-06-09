import hashlib
from dataclasses import dataclass


@dataclass
class LoginRequest:
    username: str
    password: str


@dataclass
class RegisterRequest:
    username: str
    password: str
    password_confirm: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
