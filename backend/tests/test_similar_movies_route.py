import asyncio

from app.routes import movies as movies_route


def test_similar_movies_passes_requested_page_and_returns_metadata(monkeypatch):
    calls = []

    async def fake_tmdb_get(endpoint, params=None):
        calls.append((endpoint, params))
        return {
            "page": 2,
            "total_pages": 4,
            "results": [
                {
                    "id": 55,
                    "title": "Candidate",
                    "overview": "A matching film",
                    "poster_path": "/poster.jpg",
                    "vote_average": 7.5,
                    "vote_count": 12,
                    "release_date": "2024-01-01",
                },
                {
                    "id": 56,
                    "title": "No poster",
                    "poster_path": None,
                    "vote_count": 50,
                },
            ],
        }

    monkeypatch.setattr(movies_route, "tmdb_get", fake_tmdb_get)
    result = asyncio.run(movies_route.get_similar_movies(10, page=2))

    assert calls == [("movie/10/similar", {"page": 2})]
    assert result["page"] == 2
    assert result["total_pages"] == 4
    assert [movie["id"] for movie in result["results"]] == [55]
    assert result["results"][0]["overview"] == "A matching film"
