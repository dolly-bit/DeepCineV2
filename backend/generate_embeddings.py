"""
Builds the content-based recommendation index from scratch:
  1. Embeds every movie in the DB (title + overview) with sentence-transformers
  2. Builds a FAISS similarity index over those embeddings
  3. Saves movie_index.faiss + movie_ids.npy, which ai/recommender.py loads
     at request time to power /recommend/content

Run this after importing movies (import_movies.py) - and re-run it any
time your local movie catalog changes, so the index stays in sync with
what's actually in your database.
"""

import faiss
import numpy as np

from app.database.connection import SessionLocal
from app.models.movie import Movie
from ai.embeddings import get_movie_embedding


def main():
    db = SessionLocal()

    try:
        movies = db.query(Movie).all()

        if not movies:
            print(
                "No movies found in the database. Run `python import_movies.py` "
                "first."
            )
            return

        print(f"Embedding {len(movies)} movies (this loads a ~90MB model "
              f"the first time, then runs on CPU)...")

        embeddings = []
        movie_ids = []

        for i, movie in enumerate(movies, start=1):
            embeddings.append(get_movie_embedding(movie))
            movie_ids.append(movie.id)

            if i % 50 == 0 or i == len(movies):
                print(f"  {i}/{len(movies)}")

        embeddings = np.array(embeddings).astype("float32")
        movie_ids = np.array(movie_ids)

        np.save("movie_embeddings.npy", embeddings)
        np.save("movie_ids.npy", movie_ids)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        faiss.write_index(index, "movie_index.faiss")

        print(
            f"Done. Generated embeddings + FAISS index for "
            f"{len(movie_ids)} movies."
        )
        print("Wrote: movie_embeddings.npy, movie_ids.npy, movie_index.faiss")

    finally:
        db.close()


if __name__ == "__main__":
    main()
