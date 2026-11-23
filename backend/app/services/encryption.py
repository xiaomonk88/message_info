"""Encrypt sensitive fields in record data dicts before storage; decrypt on read."""
from typing import Any, Iterable

from app.core.security import decrypt_value, encrypt_value, is_encrypted
from app.models.module import Module


def _encrypted_codes(module: Module) -> set[str]:
    codes: set[str] = set()
    for mf in module.fields:
        f = mf.field if hasattr(mf, "field") else None
        if f and f.is_encrypted:
            codes.add(f.code)
    return codes


def encrypt_record_data(module: Module, data: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict with sensitive fields encrypted (Fernet-wrapped)."""
    enc_codes = _encrypted_codes(module)
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k in enc_codes and isinstance(v, str) and not is_encrypted(v):
            out[k] = encrypt_value(v)
        else:
            out[k] = v
    return out


def decrypt_record_data(
    module: Module, data: dict[str, Any], reveal: bool = False
) -> dict[str, Any]:
    """
    Return a new dict suitable for client.

    reveal=True: decrypt and return plaintext (used for edit form, single record GET)
    reveal=False: return masked placeholder for sensitive fields (used in list views)
    """
    enc_codes = _encrypted_codes(module)
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k in enc_codes and isinstance(v, str) and is_encrypted(v):
            out[k] = decrypt_value(v) if reveal else "******"
        else:
            out[k] = v
    return out
