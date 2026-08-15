from app.database.connection import engine
from sqlalchemy import text

with engine.connect() as db:

    movies = db.execute(
        text("SELECT COUNT(*) FROM movies")
    ).scalar()

    genres = db.execute(
        text("SELECT COUNT(*) FROM genres")
    ).scalar()

    movie_genres = db.execute(
        text("SELECT COUNT(*) FROM movie_genres")
    ).scalar()

    print("================================")
    print("DATABASE CHECK")
    print("================================")

    print("Movies:", movies)
    print("Genres:", genres)
    print("Movie-Genre relationships:", movie_genres)

    print("\nMOVIES COLUMNS:")

    columns = db.execute(
        text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'movies'
            ORDER BY ordinal_position
        """)
    ).fetchall()

    for column_name, data_type in columns:
        print(f"  {column_name} -> {data_type}")

    print("\nGENRES COLUMNS:")

    columns = db.execute(
        text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'genres'
            ORDER BY ordinal_position
        """)
    ).fetchall()

    for column_name, data_type in columns:
        print(f"  {column_name} -> {data_type}")

    print("\nMOVIE_GENRES COLUMNS:")

    columns = db.execute(
        text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'movie_genres'
            ORDER BY ordinal_position
        """)
    ).fetchall()

    for column_name, data_type in columns:
        print(f"  {column_name} -> {data_type}")