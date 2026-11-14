import pytest
from unittest.mock import MagicMock

import app.database.connection as connection


def test_get_db_rolls_back_when_request_fails(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(connection, "SessionLocal", lambda: session)

    dependency = connection.get_db()
    assert next(dependency) is session

    with pytest.raises(RuntimeError, match="simulated failure"):
        dependency.throw(RuntimeError("simulated failure"))

    session.rollback.assert_called_once()
    session.close.assert_called_once()


def test_get_db_closes_session_after_success(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(connection, "SessionLocal", lambda: session)

    dependency = connection.get_db()
    assert next(dependency) is session

    with pytest.raises(StopIteration):
        next(dependency)

    session.rollback.assert_not_called()
    session.close.assert_called_once()
