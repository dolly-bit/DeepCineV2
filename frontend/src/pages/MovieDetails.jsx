import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, Clock, Star, Play } from "lucide-react";
import {
  getMovieCast,
  getSimilarMovies,
  getMovieDetails,
  getMovieTrailer,
  recordWatch,
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
  const [loading, setLoading] = useState(true);
  const [cast, setCast] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);

  async function loadMovie() {
    try {
      const [movieData, trailerData, castData, similarData] = await Promise.all([
        getMovieDetails(id),
        getMovieTrailer(id).catch(() => ({ url: null })),
        getMovieCast(id).catch(() => []),
        getSimilarMovies(id).catch(() => []),
      ]);

      setMovie(movieData);
      setTrailer(trailerData?.url || null);
      setCast(castData || []);
      setSimilarMovies(similarData || []);

      // This is the "watch_history" signal: opening a movie's details
      // page (i.e. clicking "More Info" / a poster anywhere in the app)
      // is what gets logged, and it's exactly what the collaborative-
      // filtering model trains on later.
      recordWatch(movieData.id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMovie();
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
                <div
                  key={similar.id}
                  onClick={() => navigate(`/movie/${similar.id}`)}
                  className="shrink-0 cursor-pointer"
                >
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