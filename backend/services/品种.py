"""品种树与K线样本装载。"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import Config
from app.db import rows_to_list


def list_symbols(conn) -> list[dict]:
    cur = conn.execute(
        """SELECT id, 代码, 名称, 交易所, 合约乘数, 最小跳动, 已装载, 样本起始, 样本结束
           FROM 品种 ORDER BY id"""
    )
    return rows_to_list(cur)


def get_symbol(conn, symbol_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM 品种 WHERE id=?", (symbol_id,)).fetchone()
    if not row:
        return None
    return {k: row[k] for k in row.keys()}


def load_symbol_samples(conn, symbol_id: int) -> dict | None:
    sym = get_symbol(conn, symbol_id)
    if not sym:
        return None
    path = Config.fixtures_dir() / "kline_sample.json"
    extra = 0
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        code = sym["代码"]
        for block in data.get("series", []):
            if block.get("symbol_code") != code:
                continue
            for bar in block.get("bars", []):
                exists = conn.execute(
                    "SELECT id FROM K线 WHERE 品种_id=? AND 时间=?",
                    (symbol_id, bar["time"]),
                ).fetchone()
                if exists:
                    continue
                conn.execute(
                    """INSERT INTO K线 (品种_id, 周期, 时间, 开, 高, 低, 收, 量)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        symbol_id,
                        block.get("period", "1d"),
                        bar["time"],
                        bar["open"],
                        bar["high"],
                        bar["low"],
                        bar["close"],
                        bar.get("volume", 0),
                    ),
                )
                extra += 1
    bounds = conn.execute(
        "SELECT MIN(时间) t0, MAX(时间) t1, COUNT(*) c FROM K线 WHERE 品种_id=?",
        (symbol_id,),
    ).fetchone()
    conn.execute(
        """UPDATE 品种 SET 已装载=1, 样本起始=?, 样本结束=? WHERE id=?""",
        (bounds["t0"], bounds["t1"], symbol_id),
    )
    sym = get_symbol(conn, symbol_id)
    return {"symbol": sym, "loaded_bars": extra, "total_bars": bounds["c"]}


def list_klines(conn, symbol_id: int, limit: int = 120) -> list[dict]:
    cur = conn.execute(
        """SELECT id, 品种_id, 周期, 时间, 开, 高, 低, 收, 量
           FROM K线 WHERE 品种_id=? ORDER BY 时间 DESC LIMIT ?""",
        (symbol_id, limit),
    )
    items = rows_to_list(cur)
    items.reverse()
    return items


def symbol_tree(conn) -> list[dict]:
    items = list_symbols(conn)
    groups: dict[str, list] = {}
    for s in items:
        ex = s["交易所"]
        groups.setdefault(ex, []).append(s)
    return [{"exchange": k, "children": v} for k, v in sorted(groups.items())]