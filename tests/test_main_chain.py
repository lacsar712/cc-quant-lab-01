# -*- coding: utf-8 -*-
import pytest

pytestmark = pytest.mark.asyncio


async def _login(client):
    resp = await client.post("/api/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    return resp


async def test_main_chain_backtest_and_sim(client):
    await _login(client)
    sym = await client.get("/api/symbols")
    items = (await sym.get_json()).get("items") or []
    assert len(items) >= 1
    sid = items[0]["id"]
    load = await client.post(f"/api/symbols/{sid}/load")
    assert load.status_code == 200
    strat = await client.get("/api/strategies")
    sitems = (await strat.get_json()).get("items") or []
    assert sitems
    bt = await client.post(
        "/api/backtest/run",
        json={"strategy_id": sitems[0]["id"], "symbol_id": sid, "capital": 500000},
    )
    assert bt.status_code == 200
    bt_json = await bt.get_json()
    assert bt_json.get("ok") is True
    order = await client.post(
        "/api/sim/order",
        json={"symbol_id": sid, "direction": "多", "offset": "开", "lots": 1},
    )
    assert order.status_code == 200
    oj = await order.get_json()
    assert oj.get("ok") is True
    settle = await client.post("/api/pnl/settle", json={})
    assert settle.status_code == 200
    pnl = await settle.get_json()
    assert "交易日" in pnl


async def test_rules_and_risk(client):
    await _login(client)
    rules = await client.get("/api/rules")
    assert rules.status_code == 200
    put = await client.put("/api/rules/max_lots", json={"value": "45", "note": "测试"})
    assert put.status_code == 200
    scan = await client.post("/api/risk/scan")
    assert scan.status_code == 200