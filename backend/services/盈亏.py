"""盈亏日结生成。"""
from __future__ import annotations

from datetime import date

from app.db import rows_to_list


def list_daily_pnl(conn, limit: int = 60) -> list[dict]:
    cur = conn.execute(
        """SELECT id, 交易日, 实现盈亏, 浮动盈亏, 手续费合计, 净盈亏, 收盘权益, 生成时刻
           FROM 盈亏日结 ORDER BY 交易日 DESC LIMIT ?""",
        (limit,),
    )
    return rows_to_list(cur)


def generate_daily_settlement(conn, trade_day: str | None = None) -> dict:
    day = trade_day or date.today().isoformat()
    realized = conn.execute(
        """SELECT COALESCE(SUM(浮盈),0) s FROM 仿真仓位 WHERE 状态='已平'
           AND date(开仓时间)=date(?)""",
        (day,),
    ).fetchone()["s"]
    floating = conn.execute(
        "SELECT COALESCE(SUM(浮盈),0) s FROM 仿真仓位 WHERE 状态='持仓'"
    ).fetchone()["s"]
    fees = conn.execute(
        """SELECT COALESCE(SUM(手续费),0) s FROM 仿真成交
           WHERE date(成交时间)=date(?)""",
        (day,),
    ).fetchone()["s"]
    net = realized + floating - fees
    last_eq = conn.execute(
        "SELECT 收盘权益 FROM 盈亏日结 ORDER BY 交易日 DESC LIMIT 1"
    ).fetchone()
    base = float(last_eq["收盘权益"]) if last_eq else 1_000_000.0
    close_eq = round(base + net, 2)
    exists = conn.execute("SELECT id FROM 盈亏日结 WHERE 交易日=?", (day,)).fetchone()
    if exists:
        conn.execute(
            """UPDATE 盈亏日结 SET 实现盈亏=?, 浮动盈亏=?, 手续费合计=?, 净盈亏=?, 收盘权益=?,
               生成时刻=datetime('now') WHERE 交易日=?""",
            (realized, floating, fees, net, close_eq, day),
        )
    else:
        conn.execute(
            """INSERT INTO 盈亏日结 (交易日, 实现盈亏, 浮动盈亏, 手续费合计, 净盈亏, 收盘权益)
               VALUES (?,?,?,?,?,?)""",
            (day, realized, floating, fees, net, close_eq),
        )
    row = conn.execute("SELECT * FROM 盈亏日结 WHERE 交易日=?", (day,)).fetchone()
    return {k: row[k] for k in row.keys()}


def pnl_overview(conn) -> dict:
    latest = conn.execute(
        "SELECT * FROM 盈亏日结 ORDER BY 交易日 DESC LIMIT 1"
    ).fetchone()
    week = conn.execute(
        """SELECT COALESCE(SUM(净盈亏),0) s FROM 盈亏日结
           WHERE 交易日 >= date('now', '-7 day')"""
    ).fetchone()["s"]
    if not latest:
        return {"today_net": 0, "week_net": week, "equity": 1_000_000}
    return {
        "today_net": latest["净盈亏"],
        "week_net": week,
        "equity": latest["收盘权益"],
        "trade_day": latest["交易日"],
    }