# -*- coding: utf-8 -*-
from pathlib import Path

import pytest_asyncio

ROOT = Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    from app.db import init_db
    from app.seed import seed_database

    init_db(str(db_file))
    seed_database(str(db_file))
    from app.main import app as quart_app

    async with quart_app.test_client() as c:
        yield c