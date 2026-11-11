import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, Clock, Star, Play, Bookmark, Check } from "lucide-react";
import {
  getMovieCast,
  getSimilarMovies,
  getMovieDetails,
  getMovieTrailer,
  recordWatch,
  getMyRatings, saveMovieRating, deleteMovieRating, getWatchlist, addToWatchlist, removeFromWatchlist,
} from "../services/movies";
import MovieCard from "../components/home/MovieCard";
import PosterImage from "../components/ui/PosterImage";
import BackdropImage from "../components/ui/BackdropImage";

function CastAvatar({ actor }) {
  const [failed, setFailed] = useState(false);
  const showFallback = !actor.profile_url || failed;

  return (
    <div className="text-center">
      {showFallback ? (
        <div className="flex h-40 w-full items-center justify-center rounded-lg bg-cm-surface-2">
          <span className="text-2xl font-black text-white/25">
            {actor.name?.charAt(0)?.toUpperCase() || "?"}
          </span>
        </div>
      ) : (
        <img
          src={actor.profile_url}
          alt={actor.name}
          loading="lazy"
          onError={() => setFailed(true)}
          className="h-40 w-full rounded-lg object-cover"
        />
      )}

      <h3 className="mt-2 text-sm font-semibold">{actor.name}</h3>
      <p className="text-xs text-cm-muted">{actor.character}</p>
    </div>
  );
}

export default function MovieDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [movie, setMovie] = useState(null);
  const [trailer, setTrailer] = useState(null);
  const [loadedMovieId, setLoadedMovieId] = useState(null);
  const loading = loadedMovieId !== id;
  const [cast, setCast] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [myRating, setMyRating] = useState(0);
  const [watchlisted, setWatchlisted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      getMovieDetails(id),
      getMovieTrailer(id).catch(() => ({ url: null })),
      getMovieCast(id).catch(() => []),
      getSimilarMovies(id).catch(() => []),
    ])
      .then(([movieData, trailerData, castData, similarData]) => {
        if (cancelled) return;
        setMovie(movieData);
        setTrailer(trailerData?.url || null);
        setCast(castData || []);
        setSimilarMovies(similarData || []);

        // Opening a movie details page is recorded as a watch-history signal.
        recordWatch(movieData.id);
        if (localStorage.getItem("access_token")) {
          Promise.all([getMyRatings(), getWatchlist()]).then(([ratings, watchlist]) => {
            if (cancelled) return;
            setMyRating(ratings.find((item) => item.tmdb_id === movieData.id)?.rating || 0);
            setWatchlisted(watchlist.some((item) => item.tmdb_id === movieData.id));
          }).catch((err) => console.error("Could not load movie feedback", err));
        }
      })
      .catch((err) => {
        console.error(err);
        if (!cancelled) setMovie(null);
      })
      .finally(() => {
        if (!cancelled) setLoadedMovieId(id);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cm-bg text-2xl text-white">
        Loading...
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cm-bg text-white">
        Movie not found.
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cm-bg text-white">
      {/* Backdrop */}
      <div className="relative h-[62vh]">
        <BackdropImage
          src={movie.backdrop_url}
          title={movie.title}
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-black/70" />

        <button
          onClick={() => navigate(-1)}
          className="absolute left-5 top-5 z-20 rounded-full bg-black/60 p-2.5 transition hover:bg-cm-purple"
        >
          <ArrowLeft size={18} />
        </button>

        <div className="relative z-10 mx-auto flex h-full max-w-7xl items-end gap-7 px-6 pb-9">
          <PosterImage
            src={movie.poster_url}
            title={movie.title}
            className="w-48 shrink-0 rounded-xl shadow-2xl"
            imgClassName="w-48 rounded-xl object-cover shadow-2xl"
          />

          <div className="max-w-3xl">
            <h1 className="text-3xl font-extrabold md:text-4xl">{movie.title}</h1>

            {movie.tagline && (
              <p className="mt-2 text-base italic text-cm-violet">
                {movie.tagline}
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-5 text-sm">
              <div className="flex items-center gap-1.5">
                <Star size={15} fill="var(--color-cm-amber)" className="text-cm-amber" />
                <span>{movie.vote_average?.toFixed(1) ?? "N/A"}</span>
              </div>

              <div className="flex items-center gap-1.5">
                <Calendar size={15} />
                <span>{movie.release_date || "TBA"}</span>
              </div>

              {movie.runtime ? (
                <div className="flex items-center gap-1.5">
                  <Clock size={15} />
                  <span>{movie.runtime} min</span>
                </div>
              ) : null}
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {movie.genres?.map((genre) => (
                <span
                  key={genre.id}
                  className="rounded-full border border-cm-purple bg-cm-purple/20 px-3 py-1 text-xs"
                >
                  {genre.name}
                </span>
              ))}
            </div>

            <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-300 md:text-base">
              {movie.overview}
            </p>

            <div className="dc-movie-feedback">
              <div className="dc-rating-control">
                <span>YOUR RATING</span>
                <div role="group" aria-label="Rate this movie from one to five stars">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button key={value} type="button" disabled={feedbackLoading} aria-label={"Rate " + value + " out of 5"} aria-pressed={myRating === value} onClick={async () => {
                      setFeedbackLoading(true); setFeedbackMessage("");
                      try { await saveMovieRating(movie.id, value); setMyRating(value); setFeedbackMessage("Your rating was saved."); }
                      catch (err) { console.error(err); setFeedbackMessage("Could not save your rating. Sign in and ensure this movie is in the catalogue."); }
                      finally { setFeedbackLoading(false); }
                    }}><Star size={18} fill={value <= myRating ? "currentColor" : "none"} /></button>
                  ))}
                </div>
                {myRating > 0 && <button className="dc-rating-remove" type="button" disabled={feedbackLoading} onClick={async () => {
                  setFeedbackLoading(true); setFeedbackMessage("");
                  try { await deleteMovieRating(movie.id); setMyRating(0); setFeedbackMessage("Your rating was removed."); }
                  catch (err) { console.error(err); setFeedbackMessage("Could not remove your rating."); }
                  finally { setFeedbackLoading(false); }
                }}>Clear</button>}
              </div>
              <button className={"dc-watchlist-toggle" + (watchlisted ? " saved" : "")} type="button" disabled={feedbackLoading} onClick={async () => {
                setFeedbackLoading(true); setFeedbackMessage("");
                try { if (watchlisted) { await removeFromWatchlist(movie.id); setWatchlisted(false); setFeedbackMessage("Removed from your watchlist."); } else { await addToWatchlist(movie.id); setWatchlisted(true); setFeedbackMessage("Added to your watchlist."); } }
                catch (err) { console.error(err); setFeedbackMessage("Could not update your watchlist. Sign in and ensure this movie is in the catalogue."); }
                finally { setFeedbackLoading(false); }
              }}>{watchlisted ? <Check size={15}/> : <Bookmark size={15}/>} {watchlisted ? "In My List" : "Add to My List"}</button>
              {feedbackMessage && <span className="dc-feedback-message" role="status">{feedbackMessage}</span>}
            </div>
            <div className="mt-6 flex gap-3">
              {trailer && (
                <a
                  href={trailer}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cm-purple-deep to-cm-purple px-5 py-2.5 text-sm font-semibold transition hover:brightness-110"
                >
                  <Play size={16} />
                  Watch Trailer
                </a>
              )}

              <button
                onClick={() => navigate(-1)}
                className="rounded-xl bg-white/10 px-5 py-2.5 text-sm transition hover:bg-white/20"
              >
                Back
              </button>
            </div>
          </div>
        </div>
      </div>

      {cast.length > 0 && (
        <div className="mx-auto max-w-7xl px-6 py-8">
          <h2 className="mb-5 text-xl font-bold">🎭 Cast</h2>

          <div className="grid grid-cols-3 gap-4 md:grid-cols-5 lg:grid-cols-6">
            {cast.map((actor) => (
              <CastAvatar key={actor.id} actor={actor} />
            ))}
          </div>
        </div>
      )}

      {similarMovies.length > 0 && (
        <div className="mx-auto max-w-7xl px-6 pb-10">
          <h2 className="mb-5 text-xl font-bold">🎬 Similar Movies</h2>

          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-cm-bg to-transparent" />
            <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-cm-bg to-transparent" />

            <div className="flex gap-4 overflow-x-auto scrollbar-hide pb-2">
              {similarMovies.map((similar) => (
                <div key={similar.id} className="dc-similar-card">
                  <MovieCard movie={similar} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}