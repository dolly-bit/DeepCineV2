"""Create the initial DeepCine relational schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("imdb_id", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("original_title", sa.String(length=300), nullable=True),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("poster_path", sa.String(length=500), nullable=True),
        sa.Column("backdrop_path", sa.String(length=500), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("runtime", sa.Integer(), nullable=True),
        sa.Column("vote_average", sa.Float(), nullable=True),
        sa.Column("vote_count", sa.Integer(), nullable=True),
        sa.Column("popularity", sa.Float(), nullable=True),
        sa.Column("original_language", sa.String(length=10), nullable=True),
        sa.Column("adult", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.UniqueConstraint("tmdb_id"),
    )
    op.create_index("ix_movies_id", "movies", ["id"], unique=False)

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("tmdb_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_genres_id", "genres", ["id"], unique=False)

    op.create_table(
        "movie_genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.UniqueConstraint("movie_id", "genre_id", name="uq_movie_genre"),
    )

    op.create_table(
        "watch_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("watched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_watch_history_id", "watch_history", ["id"], unique=False)

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=300), nullable=False),
        sa.Column("searched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_search_history_id", "search_history", ["id"], unique=False)

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_rating_user_movie"),
    )
    op.create_index("ix_ratings_id", "ratings", ["id"], unique=False)

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_movie"),
    )
    op.create_index("ix_watchlist_items_id", "watchlist_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_watchlist_items_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("ix_ratings_id", table_name="ratings")
    op.drop_table("ratings")
    op.drop_index("ix_search_history_id", table_name="search_history")
    op.drop_table("search_history")
    op.drop_index("ix_watch_history_id", table_name="watch_history")
    op.drop_table("watch_history")
    op.drop_table("movie_genres")
    op.drop_index("ix_genres_id", table_name="genres")
    op.drop_table("genres")
    op.drop_index("ix_movies_id", table_name="movies")
    op.drop_table("movies")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
