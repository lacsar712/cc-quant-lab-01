"""入参校验与 API 守卫辅助。"""
from __future__ import annotations


def require_fields(body: dict, fields: list[str]) -> tuple[bool, str]:
    for f in fields:
        if f not in body or body[f] in (None, ""):
            return False, f"缺少字段 {f}"
    return True, ""


def positive_int(value, name: str = "值") -> tuple[bool, str, int]:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return False, f"{name}须为整数", 0
    if n <= 0:
        return False, f"{name}须大于零", 0
    return True, "", n


def finite_float(value, name: str = "值") -> tuple[bool, str, float]:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return False, f"{name}须为数字", 0.0
    if x != x:
        return False, f"{name}无效", 0.0
    return True, "", x


def sanitize_direction(raw: str) -> str:
    if raw in ("多", "买", "long", "BUY"):
        return "多"
    if raw in ("空", "卖", "short", "SELL"):
        return "空"
    return "多"


def sanitize_offset(raw: str) -> str:
    if raw in ("开", "open", "OPEN"):
        return "开"
    if raw in ("平", "close", "CLOSE"):
        return "平"
    return "开"