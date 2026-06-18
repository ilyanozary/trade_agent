from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet() -> Fernet:
    key = current_app.config.get("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is required for exchange credentials")
    return Fernet(key.encode())


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored exchange credentials cannot be decrypted") from exc
