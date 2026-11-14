from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

import app.main as main


def test_liveness_does_not_depend_on_database():
    assert main.health_live() == {"status": "alive"}


def test_readiness_returns_ready_when_database_query_succeeds(monkeypatch):
    connection = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = connection
    monkeypatch.setattr(main.engine, "connect", lambda: context_manager)

    assert main.health_ready() == {"status": "ready", "database": "ok"}
    connection.execute.assert_called_once()


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch):
    def fail_connect():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(main.engine, "connect", fail_connect)

    with pytest.raises(HTTPException) as raised:
        main.health_ready()

    assert raised.value.status_code == 503
    assert raised.value.detail == "Database is unavailable"


def test_legacy_health_route_remains_compatible():
    assert main.health() == {"status": "alive"}
