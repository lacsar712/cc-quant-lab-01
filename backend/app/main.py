"""衡尺盘 Quart 入口：静态挂载 + REST API。"""
from __future__ import annotations

import sys
from pathlib import Path

from quart import Quart, jsonify, redirect, request, send_from_directory

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Config
from app.db import get_db, init_db
from app.seed import seed_database
from services import 会话 as auth_svc
from services import 品种 as sym_svc
from services import 策略 as strat_svc
from services import 回测 as bt_svc
from services import 仿真 as sim_svc
from services import 风控 as risk_svc
from services import 盈亏 as pnl_svc
from services import 规则 as rule_svc
from services import 说明 as help_svc
from services import 夹具 as fix_svc
from services import 校验 as val_svc

app = Quart(__name__)
app.config["SECRET_KEY"] = Config.SECRET


def _fe_dir():
    return Config.frontend_dir()


def _static_dir():
    return Config.static_dir()


def _current_user():
    return auth_svc.read_session_token(request.cookies.get(Config.SESSION_COOKIE))


def _auth_json():
    if not _current_user():
        return jsonify({"detail": "未登录"}), 401
    return None


def _bootstrap_database() -> None:
    init_db()
    seed_database()


@app.before_serving
async def boot():
    _bootstrap_database()


@app.get("/")
async def root():
    if _current_user():
        return redirect("/app/")
    return redirect("/login")


@app.get("/login")
async def login_page():
    fe = _fe_dir()
    return await send_from_directory(fe, "login.html")


@app.get("/health")
async def health():
    return jsonify({"ok": True, "lab": Config.LAB_NAME})


@app.get("/app/")
@app.get("/app/<path:subpath>")
async def spa(subpath=""):
    if not _current_user():
        return redirect("/login")
    return await send_from_directory(_fe_dir(), "index.html")


@app.get("/frontend/<path:filename>")
async def frontend_assets(filename):
    return await send_from_directory(_fe_dir(), filename)


@app.get("/static/<path:filename>")
async def static_assets(filename):
    return await send_from_directory(_static_dir(), filename)


@app.post("/api/login")
async def api_login():
    body = await request.get_json(force=True, silent=True) or {}
    user = str(body.get("username", ""))
    pwd = str(body.get("password", ""))
    if not auth_svc.validate_login(user, pwd):
        return jsonify({"ok": False, "error": "账号或密码错误"}), 400
    token = auth_svc.issue_session_token(user.strip())
    resp = jsonify({"ok": True, "user": Config.ADMIN_USER})
    resp.set_cookie(
        Config.SESSION_COOKIE,
        token,
        httponly=True,
        samesite="Lax",
        max_age=86400 * 7,
    )
    return resp


@app.post("/api/logout")
async def api_logout():
    resp = jsonify({"ok": True})
    resp.delete_cookie(Config.SESSION_COOKIE)
    return resp


@app.get("/api/me")
async def api_me():
    user = _current_user()
    if not user:
        return jsonify({"detail": "未登录"}), 401
    return jsonify(auth_svc.session_public_info(user))


@app.get("/api/overview")
async def api_overview():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        data = help_svc.lab_overview(conn)
        data["pnl"] = pnl_svc.pnl_overview(conn)
        data["activity"] = help_svc.recent_activity(conn)
    return jsonify(data)


@app.get("/api/help")
async def api_help():
    gate = _auth_json()
    if gate:
        return gate
    return jsonify({"sections": help_svc.help_sections()})


@app.get("/api/symbols/tree")
async def api_symbol_tree():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"tree": sym_svc.symbol_tree(conn)})


@app.get("/api/symbols")
async def api_symbols():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": sym_svc.list_symbols(conn)})


@app.post("/api/symbols/<int:symbol_id>/load")
async def api_load_symbol(symbol_id: int):
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        result = sym_svc.load_symbol_samples(conn, symbol_id)
    if not result:
        return jsonify({"detail": "品种不存在"}), 404
    return jsonify(result)


@app.get("/api/symbols/<int:symbol_id>/klines")
async def api_klines(symbol_id: int):
    gate = _auth_json()
    if gate:
        return gate
    limit = int(request.args.get("limit", 120))
    with get_db() as conn:
        return jsonify({"bars": sym_svc.list_klines(conn, symbol_id, limit=limit)})


@app.get("/api/strategies")
async def api_strategies():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": strat_svc.list_strategies(conn)})


@app.post("/api/strategies")
async def api_register_strategy():
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    ok, msg = val_svc.require_fields(body, ["name"])
    if not ok:
        return jsonify({"error": msg}), 400
    with get_db() as conn:
        item = strat_svc.register_strategy(
            conn,
            body["name"],
            body.get("note", ""),
            body.get("params", {}),
            body.get("status", "草稿"),
        )
    return jsonify(item), 201


@app.put("/api/strategies/<int:sid>")
async def api_update_strategy(sid: int):
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    with get_db() as conn:
        item = strat_svc.update_strategy_box(conn, sid, body.get("params", {}), body.get("status"))
    if not item:
        return jsonify({"detail": "策略不存在"}), 404
    return jsonify(item)


@app.get("/api/backtest/batches")
async def api_batches():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": bt_svc.list_batches(conn)})


@app.post("/api/backtest/run")
async def api_run_backtest():
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    ok, msg = val_svc.require_fields(body, ["strategy_id", "symbol_id"])
    if not ok:
        return jsonify({"error": msg}), 400
    capital = body.get("capital")
    with get_db() as conn:
        result = bt_svc.run_backtest_batch(
            conn, int(body["strategy_id"]), int(body["symbol_id"]), capital
        )
    if not result.get("ok"):
        return jsonify(result), 400
    return jsonify(result)


@app.get("/api/backtest/batches/<int:bid>/equity")
async def api_batch_equity(bid: int):
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"points": bt_svc.batch_equity_curve(conn, bid)})


@app.get("/api/sim/positions")
async def api_positions():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        sim_svc.refresh_floating_pnl(conn)
        return jsonify({"items": sim_svc.list_positions(conn)})


@app.get("/api/sim/trades")
async def api_trades():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": sim_svc.list_trades(conn)})


@app.post("/api/sim/order")
async def api_sim_order():
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    ok, msg = val_svc.require_fields(body, ["symbol_id", "lots"])
    if not ok:
        return jsonify({"error": msg}), 400
    ok_i, msg_i, lots = val_svc.positive_int(body["lots"], "手数")
    if not ok_i:
        return jsonify({"error": msg_i}), 400
    direction = val_svc.sanitize_direction(str(body.get("direction", "多")))
    offset = val_svc.sanitize_offset(str(body.get("offset", "开")))
    price = body.get("price")
    with get_db() as conn:
        result = sim_svc.simulate_order(
            conn, int(body["symbol_id"]), direction, offset, lots, price
        )
    code = 400 if not result.get("ok") else 200
    return jsonify(result), code


@app.get("/api/risk/alerts")
async def api_alerts():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": risk_svc.list_alerts(conn)})


@app.post("/api/risk/alerts/<int:aid>/dismiss")
async def api_dismiss_alert(aid: int):
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        ok = risk_svc.dismiss_alert(conn, aid)
    if not ok:
        return jsonify({"detail": "告警不存在"}), 404
    return jsonify({"ok": True})


@app.post("/api/risk/scan")
async def api_risk_scan():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        items = risk_svc.scan_portfolio_risk(conn)
    return jsonify({"items": items})


@app.get("/api/pnl/daily")
async def api_pnl_daily():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": pnl_svc.list_daily_pnl(conn)})


@app.post("/api/pnl/settle")
async def api_pnl_settle():
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    with get_db() as conn:
        row = pnl_svc.generate_daily_settlement(conn, body.get("trade_day"))
    return jsonify(row)


@app.get("/api/rules")
async def api_rules():
    gate = _auth_json()
    if gate:
        return gate
    with get_db() as conn:
        return jsonify({"items": rule_svc.list_rules(conn)})


@app.put("/api/rules/<key>")
async def api_rule_put(key: str):
    gate = _auth_json()
    if gate:
        return gate
    body = await request.get_json(force=True, silent=True) or {}
    ok, msg = val_svc.require_fields(body, ["value"])
    if not ok:
        return jsonify({"error": msg}), 400
    with get_db() as conn:
        item = rule_svc.upsert_rule(conn, key, body["value"], body.get("note", ""))
    return jsonify(item)


@app.get("/api/fixtures")
async def api_fixtures():
    gate = _auth_json()
    if gate:
        return gate
    return jsonify({"items": fix_svc.list_fixtures(), "catalog": fix_svc.symbol_catalog_fixture()})