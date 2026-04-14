from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def db_session() -> Session:
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url, future=True)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fred_client() -> httpx.Client:
    fixture_path = Path(__file__).parent / "fixtures" / "fred" / "UNRATE.csv"
    body = fixture_path.read_text(encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/graph/fredgraph.csv"
        assert request.url.params.get("id") == "UNRATE"
        return httpx.Response(200, text=body)

    client = httpx.Client(base_url="https://fred.example.test", transport=httpx.MockTransport(handler))
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def rss_client() -> httpx.Client:
    fixture_path = Path(__file__).parent / "fixtures" / "rss" / "labor_claims.xml"
    body = fixture_path.read_text(encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://rss.example.test/corporate-ir.xml"
        return httpx.Response(200, text=body)

    client = httpx.Client(base_url="https://rss.example.test", transport=httpx.MockTransport(handler))
    try:
        yield client
    finally:
        client.close()
