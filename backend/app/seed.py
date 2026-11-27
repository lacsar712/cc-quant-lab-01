"""首次启动种子数据（品种、K线、策略、规则等）。"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import Config
from app.db import get_db, init_db

FIXTURE_SYMBOLS = [
    ("IF主连", "沪深300股指期货", "CFFEX", 300, 0.2),
    ("AU主连", "黄金期货", "SHFE", 1000, 0.02),
    ("RB主连", "螺纹钢期货", "SHFE", 10, 1.0),
    ("SC主连", "原油期货", "INE", 1000, 0.1),
    ("M主连", "豆粕期货", "DCE", 10, 1.0),
]


def _load_fixture_klines() -> list[tuple]:
    path = Config.fixtures_dir() / "kline_sample.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    sym_map = {"IF主连": 1, "AU主连": 2}
    for block in data.get("series", []):
        sym_id = sym_map.get(block.get("symbol_code"), 1)
        for bar in block.get("bars", []):
            rows.append(
                (
                    sym_id,
                    block.get("period", "1d"),
                    bar["time"],
                    bar["open"],
                    bar["high"],
                    bar["low"],
                    bar["close"],
                    bar.get("volume", 0),
                )
            )
    return rows


def seed_database(db_path: str | None = None) -> dict:
    init_db(db_path)
    summary = {"users": 0, "symbols": 0, "klines": 0, "strategies": 0, "rules": 0}
    with get_db(db_path) as conn:
        if conn.execute("SELECT COUNT(*) c FROM 用户").fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO 用户 (用户名, 显示名, 角色) VALUES (?,?,?)",
                ("admin", "首席研究员", "管理员"),
            )
            summary["users"] = 1
        if conn.execute("SELECT COUNT(*) c FROM 品种").fetchone()["c"] == 0:
            conn.executemany(
                """INSERT INTO 品种 (代码, 名称, 交易所, 合约乘数, 最小跳动, 已装载)
                   VALUES (?,?,?,?,?,0)""",
                FIXTURE_SYMBOLS,
            )
            summary["symbols"] = len(FIXTURE_SYMBOLS)
        if conn.execute("SELECT COUNT(*) c FROM 策略").fetchone()["c"] == 0:
            strategies = [
                (
                    "双均线趋势",
                    "短均线上穿长均线开多，下穿平多",
                    json.dumps({"fast": 5, "slow": 20, "stop_ticks": 8}, ensure_ascii=False),
                    "就绪",
                ),
                (
                    "布林带均值回归",
                    "触及下轨开多，触及上轨平多",
                    json.dumps({"window": 20, "width": 2.0}, ensure_ascii=False),
                    "就绪",
                ),
                (
                    "日内突破",
                    "开盘区间突破追价，收盘前强平",
                    json.dumps({"lookback": 30, "risk_pct": 0.01}, ensure_ascii=False),
                    "草稿",
                ),
            ]
            conn.executemany(
                "INSERT INTO 策略 (名称, 说明, 参数匣, 状态) VALUES (?,?,?,?)",
                strategies,
            )
            summary["strategies"] = len(strategies)
        if conn.execute("SELECT COUNT(*) c FROM 规则键值").fetchone()["c"] == 0:
            rules = [
                ("max_lots", "50", "单品种最大持仓手数"),
                ("max_daily_loss", "50000", "单日最大亏损额"),
                ("slippage_ticks", "2", "仿真滑点跳数"),
                ("commission_rate", "0.00015", "仿真手续费率"),
            ]
            conn.executemany(
                "INSERT INTO 规则键值 (键, 值, 说明) VALUES (?,?,?)",
                rules,
            )
            summary["rules"] = len(rules)
        if conn.execute("SELECT COUNT(*) c FROM K线").fetchone()["c"] == 0:
            bars = _load_fixture_klines() + _synthetic_bars()
            if not bars:
                bars = _synthetic_bars()
            conn.executemany(
                """INSERT INTO K线 (品种_id, 周期, 时间, 开, 高, 低, 收, 量)
                   VALUES (?,?,?,?,?,?,?,?)""",
                bars,
            )
            summary["klines"] = len(bars)
            conn.execute("UPDATE 品种 SET 已装载=1, 样本起始=?, 样本结束=? WHERE id IN (1,2)", ("2024-01-02", "2024-03-29"))
        if conn.execute("SELECT COUNT(*) c FROM 盈亏日结").fetchone()["c"] == 0:
            conn.execute(
                """INSERT INTO 盈亏日结 (交易日, 实现盈亏, 浮动盈亏, 手续费合计, 净盈亏, 收盘权益)
                   VALUES (?,?,?,?,?,?)""",
                ("2024-03-28", 12500.0, -3200.0, 890.0, 8410.0, 1008410.0),
            )
    return summary


def _synthetic_bars() -> list[tuple]:
    rows = []
    price = 3800.0
    for i in range(60):
        day = f"2024-01-{i % 28 + 2:02d}"
        o = price
        h = price + 15
        low = price - 12
        c = price + (i % 5 - 2) * 3
        rows.append((1, "1d", day, o, h, low, c, 120000 + i * 1000))
        price = c
    gold = 480.0
    for i in range(40):
        day = f"2024-02-{i % 28 + 1:02d}"
        o = gold
        h = gold + 2.5
        low = gold - 2.0
        c = gold + (i % 3 - 1) * 0.8
        rows.append((2, "1d", day, o, h, low, c, 80000 + i * 500))
        gold = c
    return rows