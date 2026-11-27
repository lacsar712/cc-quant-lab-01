"""研究台说明与健康摘要。"""
from __future__ import annotations

from app.config import Config
from app.db import rows_to_list


def lab_overview(conn) -> dict:
    counts = {}
    for table in ("品种", "策略", "回测批次", "仿真成交", "风控告警", "盈亏日结"):
        counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
    open_alerts = conn.execute(
        "SELECT COUNT(*) c FROM 风控告警 WHERE 已处置=0"
    ).fetchone()["c"]
    return {
        "lab": Config.LAB_NAME,
        "product": Config.PRODUCT,
        "offline": True,
        "counts": counts,
        "open_alerts": open_alerts,
        "main_chain": [
            "装载品种与K线样本",
            "登记策略参数匣",
            "跑回测批",
            "仿真开平仓",
            "风控尺拦截",
            "盈亏日结",
        ],
    }


def help_sections() -> list[dict]:
    return [
        {
            "title": "研究总览",
            "body": "登录后默认三栏研究台：左品种树与策略，中K线与回测曲线，右仓位成交与告警。",
        },
        {
            "title": "离线声明",
            "body": "衡尺盘不接真实交易所，无 API 密钥，成交均为本地仿真。",
        },
        {
            "title": "风控尺",
            "body": "规则页可调最大手数与日亏损线，超额下单写入告警并拒绝。",
        },
    ]


def recent_activity(conn, limit: int = 15) -> list[dict]:
    cur = conn.execute(
        """SELECT '回测' AS 类型, 批次号 AS 标记, 运行时刻 AS 时刻, 状态 AS 状态 FROM 回测批次
           UNION ALL
           SELECT '成交', 回执号, 成交时间, 开平 FROM 仿真成交
           ORDER BY 时刻 DESC LIMIT ?""",
        (limit,),
    )
    return rows_to_list(cur)