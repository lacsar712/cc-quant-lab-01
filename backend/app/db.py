"""SQLite 架构与连接（衡尺盘业务表）。"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import Config

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS 用户 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    用户名 TEXT NOT NULL UNIQUE,
    显示名 TEXT NOT NULL,
  角色 TEXT NOT NULL DEFAULT '研究员',
  创建时间 TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS 品种 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    代码 TEXT NOT NULL UNIQUE,
    名称 TEXT NOT NULL,
    交易所 TEXT NOT NULL,
    合约乘数 REAL NOT NULL DEFAULT 1,
    最小跳动 REAL NOT NULL DEFAULT 0.01,
    已装载 INTEGER NOT NULL DEFAULT 0,
    样本起始 TEXT,
    样本结束 TEXT
);

CREATE TABLE IF NOT EXISTS K线 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    品种_id INTEGER NOT NULL,
    周期 TEXT NOT NULL DEFAULT '1d',
    时间 TEXT NOT NULL,
    开 REAL NOT NULL,
    高 REAL NOT NULL,
    低 REAL NOT NULL,
    收 REAL NOT NULL,
    量 REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (品种_id) REFERENCES 品种(id)
);

CREATE INDEX IF NOT EXISTS idx_kline_sym ON K线(品种_id, 时间);

CREATE TABLE IF NOT EXISTS 策略 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    名称 TEXT NOT NULL,
    说明 TEXT,
    参数匣 TEXT NOT NULL DEFAULT '{}',
    状态 TEXT NOT NULL DEFAULT '草稿',
    创建者 TEXT NOT NULL DEFAULT 'admin',
    更新时间 TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS 回测批次 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    批次号 TEXT NOT NULL UNIQUE,
    策略_id INTEGER NOT NULL,
    品种_id INTEGER NOT NULL,
    起始资金 REAL NOT NULL,
    结束资金 REAL,
    状态 TEXT NOT NULL DEFAULT '排队',
    胜率 REAL,
    最大回撤 REAL,
    运行时刻 TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (策略_id) REFERENCES 策略(id),
    FOREIGN KEY (品种_id) REFERENCES 品种(id)
);

CREATE TABLE IF NOT EXISTS 权益点 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    回测批次_id INTEGER NOT NULL,
    序号 INTEGER NOT NULL,
    时间 TEXT NOT NULL,
    净值 REAL NOT NULL,
    持仓市值 REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (回测批次_id) REFERENCES 回测批次(id)
);

CREATE TABLE IF NOT EXISTS 仿真仓位 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    品种_id INTEGER NOT NULL,
    方向 TEXT NOT NULL,
    手数 INTEGER NOT NULL,
    开仓价 REAL NOT NULL,
    浮盈 REAL NOT NULL DEFAULT 0,
    状态 TEXT NOT NULL DEFAULT '持仓',
    开仓时间 TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (品种_id) REFERENCES 品种(id)
);

CREATE TABLE IF NOT EXISTS 仿真成交 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    品种_id INTEGER NOT NULL,
    方向 TEXT NOT NULL,
    开平 TEXT NOT NULL,
    手数 INTEGER NOT NULL,
    成交价 REAL NOT NULL,
    手续费 REAL NOT NULL DEFAULT 0,
    成交时间 TEXT NOT NULL DEFAULT (datetime('now')),
    回执号 TEXT NOT NULL UNIQUE,
    FOREIGN KEY (品种_id) REFERENCES 品种(id)
);

CREATE TABLE IF NOT EXISTS 风控告警 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    级别 TEXT NOT NULL,
    类别 TEXT NOT NULL,
    摘要 TEXT NOT NULL,
    详情 TEXT,
    已处置 INTEGER NOT NULL DEFAULT 0,
    产生时间 TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS 盈亏日结 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    交易日 TEXT NOT NULL UNIQUE,
    实现盈亏 REAL NOT NULL DEFAULT 0,
    浮动盈亏 REAL NOT NULL DEFAULT 0,
    手续费合计 REAL NOT NULL DEFAULT 0,
    净盈亏 REAL NOT NULL DEFAULT 0,
    收盘权益 REAL NOT NULL,
    生成时刻 TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS 规则键值 (
    键 TEXT PRIMARY KEY,
    值 TEXT NOT NULL,
    说明 TEXT,
    更新时间 TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or Config.database()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db(db_path: str | None = None):
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with get_db(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def row_to_dict(row: sqlite3.Row | None):
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def rows_to_list(cur) -> list[dict]:
    return [row_to_dict(r) for r in cur.fetchall()]