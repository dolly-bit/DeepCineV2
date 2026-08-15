"""
Used only by the offline `generate_embeddings.py` script - not imported by
the running API - but kept lazy for consistency and so importing this
module never has a side effect of loading a ~90MB transformer model.
"""

_model = None


def _get_model():
    global _model

    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model


def get_movie_embedding(movie):
    text = f"""
    Title: {movie.title}
    Overview: {movie.overview or ""}
    Language: {movie.original_language or ""}
    """

    return _get_model().encode(text)
