import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.routes.watch_history import add_watch_history
from app.models import Movie, WatchHistory


class WatchHistoryRouteTests(unittest.TestCase):
    def test_rejects_movie_missing_from_local_catalog(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as raised:
            add_watch_history(
                tmdb_id=999999,
                db=db,
                current_user=SimpleNamespace(id=7),
            )

        self.assertEqual(raised.exception.status_code, 404)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_saves_history_for_catalog_movie(self):
        db = MagicMock()
        movie = SimpleNamespace(tmdb_id=550)
        db.query.return_value.filter.return_value.first.return_value = movie

        response = add_watch_history(
            tmdb_id=550,
            db=db,
            current_user=SimpleNamespace(id=7),
        )

        self.assertEqual(response, {"message": "Watch history saved"})
        db.query.assert_called_once_with(Movie)
        db.add.assert_called_once()
        saved_history = db.add.call_args.args[0]
        self.assertIsInstance(saved_history, WatchHistory)
        self.assertEqual(saved_history.user_id, 7)
        self.assertEqual(saved_history.tmdb_id, 550)
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
