import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Sparkles, X } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import { searchMovies, recordSearch } from "../services/movies";
import MovieCard from "../components/home/MovieCard";

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);

    // Record this search against the user's history — this is what
    // powers "Because you searched..." and improves future personalized
    // and collaborative-filtering recommendations for this account.
    recordSearch(query);

    try {
      const data = await searchMovies(query);
      setMovies(data);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-cm-bg text-white">
      <Navbar />

      <div className="px-8 py-10">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-4xl font-bold">
            🔍 Search Movies
          </h1>

          <button
            type="button"
            onClick={() => navigate("/home")}
            aria-label="Close search"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-cm-line bg-white/5 text-slate-300 transition hover:bg-white/10 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <p className="text-sm text-slate-400 mb-8">
          Every search helps DeepCine's recommendation engine learn your taste.
        </p>

        <div className="flex gap-4 mb-6">

          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search movies..."
            className="flex-1 rounded-xl bg-zinc-900 p-4 outline-none border border-zinc-700 focus:border-purple-500 transition"
          />

          <button
            onClick={handleSearch}
            className="bg-purple-600 hover:bg-purple-700 px-6 rounded-xl flex items-center gap-2 font-semibold transition"
          >
            <Search size={18} />
            Search
          </button>

        </div>

        {searched && !loading && query.trim() && (
          <button
            onClick={() =>
              navigate("/recommend", { state: { search: query.trim() } })
            }
            className="mb-10 flex items-center gap-2 rounded-full border border-purple-500/40 bg-purple-500/10 px-5 py-2.5 text-sm font-medium text-purple-200 transition hover:bg-purple-500/20"
          >
            <Sparkles size={16} />
            See personalized &amp; collaborative-filtering picks based on "{query.trim()}"
          </button>
        )}

        {loading && (
          <p className="text-gray-400">Searching...</p>
        )}

        {!loading && searched && movies.length === 0 && (
          <p className="text-gray-400">No movies found for "{query}".</p>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">

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
      </div>
    </div>
  );
}