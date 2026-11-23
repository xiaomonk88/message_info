"""Validate dynamic record data against module field definitions."""
import json
import re
from typing import Any

from app.models.field import Field
from app.models.module import Module, ModuleField
from app.schemas.field import FIELD_TYPES


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


def _coerce(field: Field, value: Any) -> Any:
    """Coerce raw value into a normalized form. Raise ValueError on bad input."""
    if value is None or value == "":
        return None

    t = field.type
    if t in ("text", "textarea", "url", "email", "password", "date", "datetime"):
        return str(value)
    if t == "number":
        try:
            if isinstance(value, bool):
                raise ValueError("not a number")
            f = float(value)
            return int(f) if f.is_integer() else f
        except (TypeError, ValueError) as e:
            raise ValueError(f"not a valid number: {value}") from e
    if t == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)
    if t == "select":
        return str(value)
    if t == "multiselect":
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        raise ValueError("multiselect requires list")
    if t in ("image", "file"):
        # Expected as relative path string under uploads/
        return str(value)
    if t == "json":
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid json: {e}") from e
        raise ValueError("json field requires object/array/json string")
    return value


def _validate_options(field: Field, value: Any) -> str | None:
    """Run option-based constraints (regex, min/max, choices). Returns error message or None."""
    if value is None:
        return None
    options: dict = {}
    if field.options:
        try:
            options = json.loads(field.options) or {}
        except (json.JSONDecodeError, TypeError):
            options = {}

    t = field.type
    if t in ("text", "textarea", "url", "email", "password"):
        max_length = options.get("maxLength")
        if max_length and isinstance(value, str) and len(value) > max_length:
            return f"长度不得超过 {max_length}"
        pattern = options.get("pattern")
        if pattern and isinstance(value, str):
            try:
                if not re.match(pattern, value):
                    return f"格式不符合要求"
            except re.error:
                pass
        if t == "email" and isinstance(value, str):
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                return "邮箱格式不正确"
        if t == "url" and isinstance(value, str):
            if not re.match(r"^https?://", value):
                return "URL 必须以 http:// 或 https:// 开头"
    elif t == "number":
        min_v = options.get("min")
        max_v = options.get("max")
        if min_v is not None and value < min_v:
            return f"不得小于 {min_v}"
        if max_v is not None and value > max_v:
            return f"不得大于 {max_v}"
    elif t in ("select", "multiselect"):
        choices = options.get("choices") or []
        valid_values = {c.get("value") if isinstance(c, dict) else c for c in choices}
        if valid_values:
            if t == "select" and value not in valid_values:
                return "选项不在可选范围"
            if t == "multiselect":
                bad = [v for v in value if v not in valid_values]
                if bad:
                    return f"以下选项不合法：{','.join(bad)}"
    return None


def validate_record_data(
    module: Module, raw: dict[str, Any], partial: bool = False
) -> dict[str, Any]:
    """
    Validate and coerce record data against module's field config.

    Args:
        module: with .fields preloaded (ModuleField with .field)
        raw: incoming dict
        partial: if True, missing required fields are not flagged (used in PATCH)

    Returns:
        normalized data dict, only containing keys defined by the module's fields
    """
    errors: dict[str, str] = {}
    out: dict[str, Any] = {}

    for mf in module.fields:
        field = mf.field if hasattr(mf, "field") and mf.field else None
        if not field:
            continue
        code = field.code
        present = code in raw
        value = raw.get(code)

        if not present:
            if mf.is_required and not partial:
                errors[code] = f"{field.name} 为必填项"
            continue

        try:
            coerced = _coerce(field, value)
        except ValueError as e:
            errors[code] = f"{field.name}: {e}"
            continue

        if mf.is_required and (coerced is None or coerced == ""):
            errors[code] = f"{field.name} 为必填项"
            continue

        msg = _validate_options(field, coerced)
        if msg:
            errors[code] = f"{field.name}: {msg}"
            continue

        if coerced is not None:
            out[code] = coerced

    if errors:
        raise ValidationError(errors)
    return out
