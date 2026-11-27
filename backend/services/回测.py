"""回测批调度与权益曲线写入。"""
from __future__ import annotations

import random
from datetime import datetime

from app.config import Config
from app.db import rows_to_list

from services import 品种 as sym_svc
from services import 策略 as strat_svc


def _batch_code() -> str:
    return "BT" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))


def list_batches(conn) -> list[dict]:
    cur = conn.execute(
        """SELECT b.id, b.批次号, b.策略_id, b.品种_id, b.起始资金, b.结束资金,
                  b.状态, b.胜率, b.最大回撤, b.运行时刻,
                  s.名称 AS 策略名, p.代码 AS 品种代码
           FROM 回测批次 b
           JOIN 策略 s ON s.id = b.策略_id
           JOIN 品种 p ON p.id = b.品种_id
           ORDER BY b.id DESC"""
    )
    return rows_to_list(cur)


def run_backtest_batch(conn, strategy_id: int, symbol_id: int, capital: float | None = None) -> dict:
    strat = strat_svc.get_strategy(conn, strategy_id)
    sym = sym_svc.get_symbol(conn, symbol_id)
    if not strat or not sym:
        return {"ok": False, "error": "策略或品种不存在"}
    bars = sym_svc.list_klines(conn, symbol_id, limit=200)
    if len(bars) < 10:
        return {"ok": False, "error": "K线样本不足，请先装载品种"}
    start_cap = float(capital or Config.DEFAULT_CAPITAL)
    code = _batch_code()
    conn.execute(
        """INSERT INTO 回测批次 (批次号, 策略_id, 品种_id, 起始资金, 状态)
           VALUES (?,?,?,?, '运行中')""",
        (code, strategy_id, symbol_id, start_cap),
    )
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    equity = start_cap
    peak = start_cap
    max_dd = 0.0
    wins = 0
    trades = 0
    params = strat.get("参数对象") or {}
    fast = int(params.get("fast", 5))
    slow = int(params.get("slow", 20))
    closes = [b["收"] for b in bars]
    for i in range(len(closes)):
        if i >= slow and i > 0:
            ma_f = sum(closes[i - fast : i]) / fast
            ma_s = sum(closes[i - slow : i]) / slow
            signal = 1 if ma_f > ma_s else -1
            ret = (closes[i] - closes[i - 1]) / closes[i - 1] * signal
            equity *= 1 + ret * 0.35
            trades += 1
            if ret > 0:
                wins += 1
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak else 0
        max_dd = max(max_dd, dd)
        conn.execute(
            """INSERT INTO 权益点 (回测批次_id, 序号, 时间, 净值, 持仓市值)
               VALUES (?,?,?,?,?)""",
            (bid, i + 1, bars[i]["时间"], round(equity, 2), round(equity * 0.3, 2)),
        )
    win_rate = (wins / trades) if trades else 0
    conn.execute(
        """UPDATE 回测批次 SET 结束资金=?, 状态='完成', 胜率=?, 最大回撤=? WHERE id=?""",
        (round(equity, 2), round(win_rate, 4), round(max_dd, 4), bid),
    )
    return {
        "ok": True,
        "batch_id": bid,
        "batch_code": code,
        "start_capital": start_cap,
        "end_capital": round(equity, 2),
        "win_rate": round(win_rate, 4),
        "max_drawdown": round(max_dd, 4),
    }


def batch_equity_curve(conn, batch_id: int) -> list[dict]:
    cur = conn.execute(
        """SELECT 序号, 时间, 净值, 持仓市值 FROM 权益点
           WHERE 回测批次_id=? ORDER BY 序号""",
        (batch_id,),
    )
    return rows_to_list(cur)