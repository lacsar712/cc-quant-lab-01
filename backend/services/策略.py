"""策略参数匣登记与维护。"""
from __future__ import annotations

import json

from app.db import rows_to_list


def list_strategies(conn) -> list[dict]:
    cur = conn.execute(
        """SELECT id, 名称, 说明, 参数匣, 状态, 创建者, 更新时间 FROM 策略 ORDER BY id"""
    )
    items = rows_to_list(cur)
    for it in items:
        try:
            it["参数对象"] = json.loads(it.pop("参数匣", "{}"))
        except json.JSONDecodeError:
            it["参数对象"] = {}
    return items


def get_strategy(conn, sid: int) -> dict | None:
    row = conn.execute("SELECT * FROM 策略 WHERE id=?", (sid,)).fetchone()
    if not row:
        return None
    d = {k: row[k] for k in row.keys()}
    try:
        d["参数对象"] = json.loads(d.pop("参数匣", "{}"))
    except json.JSONDecodeError:
        d["参数对象"] = {}
    return d


def register_strategy(conn, name: str, note: str, params: dict, status: str = "草稿") -> dict:
    payload = json.dumps(params or {}, ensure_ascii=False)
    conn.execute(
        """INSERT INTO 策略 (名称, 说明, 参数匣, 状态) VALUES (?,?,?,?)""",
        (name.strip(), (note or "").strip(), payload, status),
    )
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return get_strategy(conn, sid)


def update_strategy_box(conn, sid: int, params: dict, status: str | None = None) -> dict | None:
    item = get_strategy(conn, sid)
    if not item:
        return None
    payload = json.dumps(params or {}, ensure_ascii=False)
    if status:
        conn.execute(
            "UPDATE 策略 SET 参数匣=?, 状态=?, 更新时间=datetime('now') WHERE id=?",
            (payload, status, sid),
        )
    else:
        conn.execute(
            "UPDATE 策略 SET 参数匣=?, 更新时间=datetime('now') WHERE id=?",
            (payload, sid),
        )
    return get_strategy(conn, sid)