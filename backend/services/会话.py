"""登录会话与鉴权。"""
from __future__ import annotations

from itsdangerous import BadSignature, URLSafeSerializer

from app.config import Config


def make_serializer() -> URLSafeSerializer:
    return URLSafeSerializer(Config.SECRET, salt="hengchi-quant-v1")


def issue_session_token(username: str) -> str:
    ser = make_serializer()
    return ser.dumps({"user": username, "lab": Config.PRODUCT})


def read_session_token(raw: str | None) -> str | None:
    if not raw:
        return None
    ser = make_serializer()
    try:
        data = ser.loads(raw)
    except BadSignature:
        return None
    user = data.get("user") if isinstance(data, dict) else None
    if user != Config.ADMIN_USER:
        return None
    return user


def validate_login(username: str, password: str) -> bool:
    u = (username or "").strip()
    return u == Config.ADMIN_USER and password == Config.ADMIN_PASSWORD


def session_public_info(username: str) -> dict:
    return {
        "user": username,
        "lab": Config.LAB_NAME,
        "product": Config.PRODUCT,
        "domain": "量化交易",
        "offline": True,
    }