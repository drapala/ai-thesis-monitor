from __future__ import annotations

import os

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
