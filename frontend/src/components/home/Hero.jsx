import { ArrowRight, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { searchMovies, recordSearch } from "../../services/movies";

const fallbackMovies = [
  {
    id: 1,
    title: "A softer watchlist starts here",
    overview: "A calm, cinematic pick for a slow evening with warm lighting and heartfelt storytelling.",
    release_date: "2024-03-14",
    vote_average: 8.4,
    poster_path: "/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
  },
  {
    id: 2,
    title: "Midnight in the city",
    overview: "A moody, neon-lit story that turns every night out into an unforgettable memory.",
    release_date: "2023-11-02",
    vote_average: 7.9,
    poster_path: "/8UlWHLMpgZm9bx6QYh0NFoq67TZ.jpg",
  },
  {
    id: 3,
    title: "Quiet skies",
    overview: "A reflective journey that balances hope, nostalgia, and the feeling of setting sail again.",
    release_date: "2022-07-20",
    vote_average: 8.1,
    poster_path: "/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
  },
];

export default function Hero({ movies = [] }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeMovieIndex, setActiveMovieIndex] = useState(0);

  const featuredMovies = useMemo(() => {
    const source = Array.isArray(movies) && movies.length > 0 ? movies : fallbackMovies;

    return source.slice(0, 4).map((movie) => {
      const posterPath = movie.poster_path || movie.poster_url || movie.backdrop_url;

      return {
        id: movie.id || movie.tmdb_id || movie.title,
        title: movie.title || "Featured movie",
        overview:
          movie.overview ||
          movie.description ||
          "Curated for your next cozy night.",
        release_date: movie.release_date || "Coming soon",
        vote_average: movie.vote_average ?? 8.5,
        poster_path: posterPath,
      };
    });
  }, [movies]);

  useEffect(() => {
    if (featuredMovies.length <= 1) return;

    const timer = setInterval(() => {
      setActiveMovieIndex((prev) => (prev + 1) % featuredMovies.length);
    }, 5000);

    return () => clearInterval(timer);
  }, [featuredMovies.length]);

  const activeMovie = featuredMovies[activeMovieIndex] || featuredMovies[0];

  const getPosterUrl = (movie) => {
    if (!movie?.poster_path) return "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg";
    if (movie.poster_path.startsWith("http")) return movie.poster_path;
    return `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    recordSearch(query);

    try {
      const searchedMovies = await searchMovies(query);

      navigate("/recommend", {
        state: {
          search: query,
          movies: searchedMovies,
        },
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <section className="relative overflow-hidden px-6 lg:px-10 pt-14 pb-16 min-h-[82vh] bg-[#07070d] text-white">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: "radial-gradient(circle at top right, rgba(99,102,241,0.14), transparent 24%), radial-gradient(circle at bottom left, rgba(139,92,246,0.08), transparent 22%)",
        }}
      />

      <div className="pointer-events-none absolute top-10 left-10 h-28 w-28 rounded-full bg-slate-500/10 blur-3xl animate-float" />
      <div className="pointer-events-none absolute bottom-16 right-10 h-24 w-24 rounded-full bg-purple-500/10 blur-3xl animate-float animation-delay-2000" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-linear-to-t from-[#07070d] to-transparent" />

      <div className="relative z-10 mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1.05fr_0.95fr] items-center">
        <div className="space-y-6">
<div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300 backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-slate-300/70 animate-pulse" />
            Tailored recommendations that feel effortless
          </div>

          <h1 className="text-2xl font-semibold leading-tight text-white sm:text-3xl lg:text-[2.75rem]">
            Find calm, curated movie picks for your next cozy night.
          </h1>

          <p className="max-w-2xl text-xs text-slate-300 sm:text-sm">
            DeepCine learns the stories you love and surfaces movies that feel just right for your mood — without the noise.
          </p>

          <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto]">
            <div className="flex overflow-hidden rounded-full border border-white/10 bg-[#11121b] shadow-[0_32px_80px_rgba(8,15,32,0.24)]">
              <input
                type="text"
                placeholder="Search for a movie or genre"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                className="flex-1 bg-transparent px-5 py-4 text-white placeholder:text-slate-500 outline-none"
              />
              <button
                onClick={handleSearch}
                className="inline-flex items-center justify-center rounded-full bg-linear-to-r from-slate-600 via-purple-600 to-fuchsia-500 px-6 text-white transition hover:from-slate-700 hover:to-fuchsia-600"
              >
                <Search size={20} />
              </button>
            </div>

            <button
              onClick={() => navigate("/signup")}
              className="inline-flex items-center justify-center rounded-full bg-linear-to-r from-slate-600 via-purple-600 to-fuchsia-500 px-6 py-3 text-xs font-semibold text-[#07070d] shadow-lg shadow-purple-600/20 transition hover:scale-[1.02]"
            >
              Discover now
              <ArrowRight size={18} className="ml-2" />
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Curated movies", value: "12K+" },
              { label: "Smart filters", value: "3" },
              { label: "Quick picks", value: "0.5s" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-3xl border border-white/10 bg-white/5 p-4 text-white backdrop-blur-sm"
              >
                <p className="text-lg font-semibold">{item.value}</p>
                <p className="mt-2 text-[11px] uppercase tracking-[0.24em] text-slate-400">
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="relative w-full max-w-110 rounded-[36px] border border-white/10 bg-[#0a0914]/80 p-5 shadow-[0_36px_100px_rgba(99,102,241,0.12)]">
            <div className="absolute inset-0 rounded-[36px] border border-slate-500/10 blur-xl opacity-20" />
            <div className="relative overflow-hidden rounded-4xl bg-[#0f0c18]">
              <img
                key={activeMovie?.id}
                src={getPosterUrl(activeMovie)}
                alt={activeMovie?.title || "Movie hero"}
                className="h-90 w-full object-cover transition duration-700 hover:scale-105"
              />
              <div className="absolute inset-0 bg-linear-to-t from-[#07070d]/90 via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-5 text-white">
                <p className="text-xs uppercase tracking-[0.32em] text-slate-400">Featured pick</p>
                <h2 className="mt-2 text-2xl font-semibold">{activeMovie?.title}</h2>
                <p className="mt-2 max-w-xl text-sm text-slate-300 line-clamp-3">
                  {activeMovie?.overview}
                </p>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between gap-3">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4 text-white flex-1">
                <p className="text-xs text-slate-400">Release</p>
                <p className="mt-2 text-sm font-semibold">{activeMovie?.release_date}</p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4 text-white flex-1">
                <p className="text-xs text-slate-400">Rating</p>
                <p className="mt-2 text-sm font-semibold">{activeMovie?.vote_average?.toFixed?.(1) ?? activeMovie?.vote_average} / 10</p>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-center gap-2">
              {featuredMovies.map((movie, index) => (
                <button
                  key={movie.id}
                  type="button"
                  onClick={() => setActiveMovieIndex(index)}
                  className={`h-2.5 rounded-full transition ${index === activeMovieIndex ? "w-8 bg-purple-500" : "w-2.5 bg-white/30"}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
