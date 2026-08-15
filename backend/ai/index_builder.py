

from pathlib import Path

from app.models.movie import Movie
from ai.embeddings import get_movie_embedding
import faiss
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent


def build_recommendation_index(db, verbose: bool = True):
    """Rebuilds movie_embeddings.npy / movie_ids.npy / movie_index.faiss
    from whatever movies currently exist in the DB. Returns the number of
    movies indexed, or 0 if there were none to index."""

    # Imported here, not at module level: this module is now reachable
    # from app.main's startup chain (main -> schedular -> movie_updater
    # -> index_builder), and importing faiss/numpy eagerly at module
    # scope would reintroduce the exact slow-boot problem already fixed
    # elsewhere (see ai/recommender.py) - every server start would pay
    # for loading these before accepting a single request.
   

    movies = db.query(Movie).all()

    if not movies:
        if verbose:
            print(
                "No movies found in the database - nothing to index. Run "
                "`python import_movies.py` first."
            )
        return 0

    if verbose:
        print(
            f"Embedding {len(movies)} movies (loads a ~90MB model the "
            f"first time, then runs on CPU)..."
        )

    embeddings = []
    movie_ids = []

    for i, movie in enumerate(movies, start=1):
        embeddings.append(get_movie_embedding(movie))
        movie_ids.append(movie.id)

        if verbose and (i % 100 == 0 or i == len(movies)):
            print(f"  {i}/{len(movies)}")

    embeddings = np.array(embeddings).astype("float32")
    movie_ids = np.array(movie_ids)

    np.save(str(BASE_DIR / "movie_embeddings.npy"), embeddings)
    np.save(str(BASE_DIR / "movie_ids.npy"), movie_ids)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    faiss.write_index(index, str(BASE_DIR / "movie_index.faiss"))

    if verbose:
        print(
            f"Done. Indexed {len(movie_ids)} movies -> movie_index.faiss"
        )

    return len(movie_ids)
