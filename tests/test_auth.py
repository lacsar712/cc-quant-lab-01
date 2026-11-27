# -*- coding: utf-8 -*-
import pytest

pytestmark = pytest.mark.asyncio


async def test_login_page_has_password_hint(client):
    resp = await client.get("/login")
    assert resp.status_code == 200
    body = await resp.get_data(as_text=True)
    assert "登录" in body
    assert "密码" in body


async def test_login_flow(client):
    bad = await client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 400
    ok = await client.post("/api/login", json={"username": "admin", "password": "123456"})
    assert ok.status_code == 200
    data = await ok.get_json()
    assert data.get("ok") is True
    cookies = ok.headers.getlist("Set-Cookie")
    assert any("hengchi_session" in c for c in cookies)