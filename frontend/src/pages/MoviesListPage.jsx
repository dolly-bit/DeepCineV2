import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import MovieCard from "../components/home/MovieCard";
import { getTrendingMovies, getTopRatedMovies, getUpcomingMovies, getPersonalizedRecommendations } from "../services/movies";

export default function MoviesListPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const mode = location.state?.mode || "trending";
  const title = location.state?.title || "Movies";

  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const loadMovies = async () => {
      try {
        setLoading(true);
        setError("");

        let data = [];

        if (mode === "trending") {
          data = await getTrendingMovies();
        } else if (mode === "recommended") {
          const userId = localStorage.getItem("user_id");
          if (!userId) {
            data = [];
          } else {
            data = await getPersonalizedRecommendations(userId);
          }
        } else if (mode === "top-rated") {
          data = await getTopRatedMovies();
        } else if (mode === "upcoming") {
          data = await getUpcomingMovies();
          const today = new Date().toISOString().slice(0, 10);
          data = (data || []).filter((movie) => movie.release_date && movie.release_date >= today);
        }

        if (isMounted) {
          setMovies(data || []);
        }
      } catch (err) {
        console.error(err);
        if (isMounted) {
          setError("We couldn't load this movie list right now.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadMovies();

    return () => {
      isMounted = false;
    };
  }, [location.state?.mode, location.state?.query]);

  const visibleMovies = useMemo(() => movies.slice(0, 50), [movies]);

  return (
    <div className="min-h-screen bg-[#08070C] text-white">
      <Navbar />

      <main className="mx-auto max-w-7xl px-6 py-10 lg:px-10">
        <div className="mb-8 overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-r from-purple-600/20 via-fuchsia-500/10 to-cyan-500/10 p-6 shadow-[0_20px_80px_rgba(15,23,42,0.35)]">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.35em] text-purple-300">Discover</p>
              <h1 className="mt-2 text-3xl font-semibold text-white">{title}</h1>
              <p className="mt-3 max-w-2xl text-sm text-slate-300">
                {mode === "recommended"
                  ? "These picks are hand-selected to feel personal, cinematic, and easy to explore."
                  : `Browse a curated collection of ${mode === "trending" ? "trending" : mode.replace("-", " ")} movies.`}
              </p>
            </div>

            <button
              onClick={() => navigate("/home")}
              className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
            >
              Back to home
            </button>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="h-[340px] animate-pulse rounded-3xl bg-zinc-800" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-red-500/20 bg-red-500/10 p-6 text-red-200">
            {error}
          </div>
        ) : visibleMovies.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-300">
            No movies available for this selection right now.
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {visibleMovies.map((movie) => (
              <div key={movie.id || movie.tmdb_id} className="cursor-pointer" onClick={() => navigate(`/movie/${movie.id || movie.tmdb_id}`)}>
                <MovieCard movie={movie} />
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
