"""夹具 JSON 读取与导入辅助。"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import Config


def list_fixtures() -> list[dict]:
    folder = Config.fixtures_dir()
    if not folder.is_dir():
        return []
    out = []
    for p in sorted(folder.glob("*.json")):
        out.append({"name": p.name, "bytes": p.stat().st_size})
    return out


def read_fixture(name: str) -> dict:
    path = Config.fixtures_dir() / name
    if not path.is_file() or ".." in name:
        return {"ok": False, "error": "文件不存在"}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"ok": True, "name": name, "data": data}


def symbol_catalog_fixture() -> dict:
    path = Config.fixtures_dir() / "symbols.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "catalog": "offline-demo",
        "items": [
            {"code": "IF主连", "name": "沪深300股指期货"},
            {"code": "AU主连", "name": "黄金期货"},
        ],
    }