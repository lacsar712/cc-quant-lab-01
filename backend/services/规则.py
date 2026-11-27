"""规则键值维护。"""
from __future__ import annotations

from app.db import rows_to_list


def list_rules(conn) -> list[dict]:
    cur = conn.execute("SELECT 键, 值, 说明, 更新时间 FROM 规则键值 ORDER BY 键")
    return rows_to_list(cur)


def get_rule(conn, key: str, default: str = "") -> str:
    row = conn.execute("SELECT 值 FROM 规则键值 WHERE 键=?", (key,)).fetchone()
    if not row:
        return default
    return str(row["值"])


def upsert_rule(conn, key: str, value: str, note: str = "") -> dict:
    conn.execute(
        """INSERT INTO 规则键值 (键, 值, 说明) VALUES (?,?,?)
           ON CONFLICT(键) DO UPDATE SET 值=excluded.值, 说明=excluded.说明,
           更新时间=datetime('now')""",
        (key.strip(), str(value), note),
    )
    row = conn.execute("SELECT * FROM 规则键值 WHERE 键=?", (key.strip(),)).fetchone()
    return {k: row[k] for k in row.keys()}