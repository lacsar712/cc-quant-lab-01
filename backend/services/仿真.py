"""仿真开平仓与成交簿。"""
from __future__ import annotations

import random
from datetime import datetime

from app.config import Config
from app.db import rows_to_list

from services import 品种 as sym_svc
from services import 规则 as rule_svc
from services import 风控 as risk_svc


def _ticket() -> str:
    return "SIM" + datetime.now().strftime("%H%M%S") + str(random.randint(10000, 99999))


def list_positions(conn) -> list[dict]:
    cur = conn.execute(
        """SELECT p.id, p.品种_id, p.方向, p.手数, p.开仓价, p.浮盈, p.状态, p.开仓时间,
                  s.代码, s.名称
           FROM 仿真仓位 p
           JOIN 品种 s ON s.id = p.品种_id
           WHERE p.状态='持仓' ORDER BY p.id DESC"""
    )
    return rows_to_list(cur)


def list_trades(conn, limit: int = 80) -> list[dict]:
    cur = conn.execute(
        """SELECT t.id, t.品种_id, t.方向, t.开平, t.手数, t.成交价, t.手续费, t.成交时间, t.回执号,
                  s.代码
           FROM 仿真成交 t
           JOIN 品种 s ON s.id = t.品种_id
           ORDER BY t.id DESC LIMIT ?""",
        (limit,),
    )
    return rows_to_list(cur)


def _last_price(conn, symbol_id: int) -> float:
    row = conn.execute(
        "SELECT 收 FROM K线 WHERE 品种_id=? ORDER BY 时间 DESC LIMIT 1",
        (symbol_id,),
    ).fetchone()
    if row:
        return float(row["收"])
    sym = sym_svc.get_symbol(conn, symbol_id)
    return 100.0 if not sym else sym.get("最小跳动", 1) * 1000


def simulate_order(
    conn,
    symbol_id: int,
    direction: str,
    offset: str,
    lots: int,
    price: float | None = None,
) -> dict:
    sym = sym_svc.get_symbol(conn, symbol_id)
    if not sym:
        return {"ok": False, "error": "品种不存在"}
    lots = int(lots)
    if lots <= 0:
        return {"ok": False, "error": "手数须为正整数"}
    direction = direction if direction in ("多", "空") else "多"
    offset = offset if offset in ("开", "平") else "开"
    px = float(price) if price else _last_price(conn, symbol_id)
    slip = int(rule_svc.get_rule(conn, "slippage_ticks", "2"))
    px += sym["最小跳动"] * slip * (1 if direction == "多" else -1)
    open_lots = conn.execute(
        "SELECT COALESCE(SUM(手数),0) c FROM 仿真仓位 WHERE 品种_id=? AND 状态='持仓'",
        (symbol_id,),
    ).fetchone()["c"]
    guard = risk_svc.check_order_guard(conn, symbol_id, offset, lots, open_lots)
    if not guard.get("ok"):
        risk_svc.raise_alert(
            conn,
            "拦截",
            "下单超额",
            guard.get("message", "风控拒绝"),
            f"品种 {sym['代码']} 请求 {offset}{lots}手",
        )
        return {"ok": False, "error": guard.get("message"), "risk": True}
    comm_rate = float(rule_svc.get_rule(conn, "commission_rate", "0.00015"))
    fee = round(px * lots * sym["合约乘数"] * comm_rate, 2)
    ticket = _ticket()
    conn.execute(
        """INSERT INTO 仿真成交 (品种_id, 方向, 开平, 手数, 成交价, 手续费, 回执号)
           VALUES (?,?,?,?,?,?,?)""",
        (symbol_id, direction, offset, lots, round(px, 4), fee, ticket),
    )
    if offset == "开":
        conn.execute(
            """INSERT INTO 仿真仓位 (品种_id, 方向, 手数, 开仓价, 浮盈, 状态)
               VALUES (?,?,?,?,0,'持仓')""",
            (symbol_id, direction, lots, round(px, 4)),
        )
    else:
        pos = conn.execute(
            """SELECT id, 手数, 开仓价 FROM 仿真仓位
               WHERE 品种_id=? AND 方向=? AND 状态='持仓' ORDER BY id LIMIT 1""",
            (symbol_id, direction),
        ).fetchone()
        if not pos:
            return {"ok": False, "error": "无可平仓位"}
        pl = (px - pos["开仓价"]) * lots * sym["合约乘数"]
        if direction == "空":
            pl = -pl
        conn.execute("UPDATE 仿真仓位 SET 状态='已平', 浮盈=? WHERE id=?", (round(pl, 2), pos["id"]))
    return {
        "ok": True,
        "ticket": ticket,
        "price": round(px, 4),
        "fee": fee,
        "symbol": sym["代码"],
        "direction": direction,
        "offset": offset,
        "lots": lots,
    }


def refresh_floating_pnl(conn) -> int:
    updated = 0
    rows = conn.execute(
        """SELECT p.id, p.品种_id, p.方向, p.手数, p.开仓价, s.合约乘数
           FROM 仿真仓位 p JOIN 品种 s ON s.id=p.品种_id WHERE p.状态='持仓'"""
    ).fetchall()
    for r in rows:
        px = _last_price(conn, r["品种_id"])
        pl = (px - r["开仓价"]) * r["手数"] * r["合约乘数"]
        if r["方向"] == "空":
            pl = -pl
        conn.execute("UPDATE 仿真仓位 SET 浮盈=? WHERE id=?", (round(pl, 2), r["id"]))
        updated += 1
    return updated