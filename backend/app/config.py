"""衡尺盘模拟研究台配置。"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]


class Config:
    LAB_NAME = "衡尺盘模拟研究台"
    PRODUCT = "衡尺盘"
    SECRET = os.environ.get("SECRET_KEY", "hengchi-quant-offline-demo")
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "123456"
    SESSION_COOKIE = "hengchi_session"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "8800"))
    MAX_POSITION_LOTS = 50
    MAX_DAILY_LOSS = 50000.0
    DEFAULT_CAPITAL = 1_000_000.0

    @staticmethod
    def database() -> str:
        raw = os.environ.get("DATABASE_PATH")
        if raw:
            return raw
        inst = BACKEND / "instance"
        inst.mkdir(parents=True, exist_ok=True)
        return str(inst / "hengchi_quant.db")

    @staticmethod
    def frontend_dir() -> Path:
        fe = ROOT / "frontend"
        return fe if fe.is_dir() else BACKEND.parent / "frontend"

    @staticmethod
    def static_dir() -> Path:
        st = ROOT / "static"
        return st if st.is_dir() else BACKEND.parent / "static"

    @staticmethod
    def fixtures_dir() -> Path:
        return ROOT / "fixtures"