"""风控尺：超额拦截与告警写库。"""
from __future__ import annotations

from app.config import Config
from app.db import rows_to_list

from services import 规则 as rule_svc


def list_alerts(conn, only_open: bool = True) -> list[dict]:
    sql = "SELECT id, 级别, 类别, 摘要, 详情, 已处置, 产生时间 FROM 风控告警"
    if only_open:
        sql += " WHERE 已处置=0"
    sql += " ORDER BY id DESC"
    return rows_to_list(conn.execute(sql))


def raise_alert(conn, level: str, category: str, summary: str, detail: str = "") -> dict:
    conn.execute(
        """INSERT INTO 风控告警 (级别, 类别, 摘要, 详情) VALUES (?,?,?,?)""",
        (level, category, summary, detail),
    )
    aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    row = conn.execute("SELECT * FROM 风控告警 WHERE id=?", (aid,)).fetchone()
    return {k: row[k] for k in row.keys()}


def dismiss_alert(conn, alert_id: int) -> bool:
    cur = conn.execute("UPDATE 风控告警 SET 已处置=1 WHERE id=?", (alert_id,))
    return cur.rowcount > 0


def check_order_guard(conn, symbol_id: int, offset: str, lots: int, open_lots: int) -> dict:
    max_lots = int(rule_svc.get_rule(conn, "max_lots", str(Config.MAX_POSITION_LOTS)))
    if offset == "开" and open_lots + lots > max_lots:
        return {
            "ok": False,
            "message": f"超过单品种上限 {max_lots} 手（当前 {open_lots}）",
        }
    daily = conn.execute(
        """SELECT COALESCE(SUM(净盈亏),0) s FROM 盈亏日结
           WHERE 交易日 = date('now')"""
    ).fetchone()["s"]
    max_loss = float(rule_svc.get_rule(conn, "max_daily_loss", str(Config.MAX_DAILY_LOSS)))
    if daily < -max_loss:
        return {"ok": False, "message": f"当日亏损已触线 {max_loss}，禁止加仓"}
    return {"ok": True}


def scan_portfolio_risk(conn) -> list[dict]:
    alerts = []
    pos = conn.execute(
        "SELECT 品种_id, SUM(手数) lots FROM 仿真仓位 WHERE 状态='持仓' GROUP BY 品种_id"
    ).fetchall()
    max_lots = int(rule_svc.get_rule(conn, "max_lots", "50"))
    for p in pos:
        if p["lots"] >= max_lots * 0.9:
            item = raise_alert(
                conn,
                "预警",
                "仓位集中",
                f"品种#{p['品种_id']} 持仓 {p['lots']} 手接近上限",
            )
            alerts.append(item)
    float_pnl = conn.execute(
        "SELECT COALESCE(SUM(浮盈),0) s FROM 仿真仓位 WHERE 状态='持仓'"
    ).fetchone()["s"]
    if float_pnl < -20000:
        item = raise_alert(
            conn,
            "预警",
            "浮动亏损",
            f"组合浮亏 {float_pnl:.2f} 元，请减仓",
        )
        alerts.append(item)
    return alerts