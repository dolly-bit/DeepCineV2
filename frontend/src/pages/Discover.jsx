import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Sparkles, X } from "lucide-react";

import Navbar from "../components/layout/Navbar";
import MovieCard from "../components/home/MovieCard";
import {
  getMoods,
  getGenres,
  getLanguages,
  discoverMovies,
} from "../services/movies";

export default function Discover() {
  const navigate = useNavigate();
  const location = useLocation();

  const [moods, setMoods] = useState([]);
  const [genres, setGenres] = useState([]);
  const [languages, setLanguages] = useState([]);

  // Pre-select a mood when arriving from the Home page's "Browse by
  // mood" section (navigate("/discover", { state: { mood: key } })).
  const [activeMood, setActiveMood] = useState(location.state?.mood || null);
  const [activeGenres, setActiveGenres] = useState([]);
  const [activeLanguage, setActiveLanguage] = useState(null);

  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtersLoading, setFiltersLoading] = useState(true);

  // Load filter options once
  useEffect(() => {
    async function loadFilters() {
      try {
        const [m, g, l] = await Promise.all([
          getMoods(),
          getGenres(),
          getLanguages(),
        ]);
        setMoods(m);
        setGenres(g);
        setLanguages(l);
      } catch (err) {
        console.error(err);
      } finally {
        setFiltersLoading(false);
      }
    }

    loadFilters();
  }, []);

  // Re-run the search whenever a filter changes
  useEffect(() => {
    async function runSearch() {
      setLoading(true);
      try {
        const data = await discoverMovies({
          mood: activeMood,
          genres: activeGenres,
          language: activeLanguage,
        });
        setMovies(data);
      } catch (err) {
        console.error(err);
        setMovies([]);
      } finally {
        setLoading(false);
      }
    }

    runSearch();
  }, [activeMood, activeGenres, activeLanguage]);

  const toggleGenre = (id) => {
    setActiveGenres((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id]
    );
  };

  const clearAll = () => {
    setActiveMood(null);
    setActiveGenres([]);
    setActiveLanguage(null);
  };

  const hasFilters = activeMood || activeGenres.length > 0 || activeLanguage;

  return (
    <div className="min-h-screen bg-cm-bg text-white">
      <Navbar />

      <section className="max-w-7xl mx-auto px-6 pt-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cm-purple">
              Discover
            </p>
            <h1 className="mt-1.5 text-2xl sm:text-3xl font-bold text-white">
              Find something to watch
            </h1>
            <p className="mt-1.5 text-sm text-slate-400">
              Mix and match mood, genre, and language — results update live.
            </p>
          </div>

          <button
            onClick={() => navigate("/home")}
            className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
          >
            Back to home
          </button>
        </div>
      </section>

      {/* Mood chips */}
      <section className="max-w-7xl mx-auto px-6 mt-6">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Mood
        </h2>
        {filtersLoading ? (
          <div className="flex gap-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-9 w-28 animate-pulse rounded-full bg-white/10" />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {moods.map((m) => (
              <button
                key={m.key}
                onClick={() =>
                  setActiveMood((prev) => (prev === m.key ? null : m.key))
                }
                title={m.description}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  activeMood === m.key
                    ? "border-cm-purple bg-cm-purple/25 text-white"
                    : "border-cm-line bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Genre chips */}
      <section className="max-w-7xl mx-auto px-6 mt-5">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Genre
        </h2>
        {filtersLoading ? (
          <div className="flex gap-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-9 w-24 animate-pulse rounded-full bg-white/10" />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {genres.map((g) => (
              <button
                key={g.id}
                onClick={() => toggleGenre(g.id)}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  activeGenres.includes(g.id)
                    ? "border-cm-cyan bg-cm-cyan/20 text-white"
                    : "border-cm-line bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
              >
                {g.name}
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Language dropdown */}
      <section className="max-w-7xl mx-auto px-6 mt-5 flex flex-wrap items-center gap-3">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Language
          </h2>
          <select
            value={activeLanguage || ""}
            onChange={(e) => setActiveLanguage(e.target.value || null)}
            className="rounded-xl border border-cm-line bg-cm-surface px-4 py-2 text-sm text-white outline-none focus:border-cm-purple"
          >
            <option value="">Any language</option>
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        {hasFilters && (
          <button
            onClick={clearAll}
            className="mt-6 flex items-center gap-1.5 rounded-full border border-cm-line bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10"
          >
            <X size={13} />
            Clear filters
          </button>
        )}
      </section>

      {/* Results */}
      <section className="max-w-7xl mx-auto px-6 mt-8 pb-16">
        {loading ? (
          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="h-[250px] animate-pulse rounded-2xl bg-zinc-800" />
            ))}
          </div>
        ) : movies.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-white/10 bg-white/5 py-16 text-center">
            <Sparkles className="text-cm-purple" size={22} />
            <p className="text-sm text-slate-400">
              No movies matched that combination — try loosening a filter.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">
            {movies.map((movie) => (
              <div
                key={movie.id}
                className="cursor-pointer"
                onClick={() => navigate(`/movie/${movie.id}`)}
              >
                <MovieCard movie={movie} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}