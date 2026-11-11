import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import MovieCard from "./home/MovieCard";
import {
  searchMovies,
  getTrendingMovies,
  recordSearch,
} from "../services/movies";

export default function SearchModal({ isOpen, onClose }) {
  const navigate = useNavigate();

  const [query, setQuery] = useState("");

  const [movies, setMovies] = useState([]);

  const [trending, setTrending] = useState([]);

  const [loading, setLoading] = useState(false);

  // Close on ESC
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKey);

    return () => {
      window.removeEventListener("keydown", handleKey);
    };
  }, [onClose]);

  // Load Trending
  useEffect(() => {
    if (!isOpen) return;

    async function loadTrending() {
      try {
        const data = await getTrendingMovies();
        setTrending(data.slice(0, 10));
      } catch (err) {
        console.error(err);
      }
    }

    loadTrending();
  }, [isOpen]);

  // Live Search
  useEffect(() => {
    if (!query.trim()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMovies([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);

      try {
        const data = await searchMovies(query);

        setMovies(data);

        // Record the search once results actually come back for it
        // (debounced already by this same timeout), so we're not
        // spamming search-history with every half-typed keystroke.
        recordSearch(query);
      } catch (err) {
        console.error(err);
      }

      setLoading(false);
    }, 400);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>

      <motion.div
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex justify-center items-start pt-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >

        <motion.div
          initial={{
            opacity: 0,
            scale: 0.95,
            y: -30,
          }}
          animate={{
            opacity: 1,
            scale: 1,
            y: 0,
          }}
          exit={{
            opacity: 0,
            scale: 0.95,
          }}
          transition={{
            duration: 0.25,
          }}
          onClick={(e) => e.stopPropagation()}
          className="dc-search-modal w-[95%] max-w-6xl h-[82vh] rounded-2xl border shadow-2xl flex flex-col overflow-hidden"
        >

          {/* Search Bar */}

          <div className="dc-search-modal-bar flex items-center gap-4 px-7 py-4 border-b">

            <Search
              size={20}
              className="dc-search-modal-icon"
            />

            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search movies..."
              className="dc-search-modal-input flex-1 bg-transparent outline-none"
            />

            <button
              type="button"
              onClick={onClose}
              aria-label="Close search"
            >
              <X
                className="dc-search-modal-close"
              />
            </button>

          </div>

          {/* Content */}

          <div className="dc-search-modal-content flex-1 overflow-y-auto px-7 py-6">
            {/* Trending Movies */}

{!query && (
  <>
    <h2 className="dc-search-section-title text-lg font-bold mb-4">
      🔥 Trending Movies
    </h2>

    <div className="relative">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-[#121212] to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-[#121212] to-transparent" />

      <div className="dc-search-trending-track flex gap-4 overflow-x-auto scrollbar-hide pb-3">
        {trending.map((movie) => (
          <div key={movie.id} onClick={onClose} className="dc-search-trending-item shrink-0" style={{ flex: "0 0 150px", width: "150px", minWidth: "150px" }}>
            <MovieCard movie={movie} />
          </div>
        ))}
      </div>
    </div>
  </>
)}

{/* Search Results */}

{query && (
  <>
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h2 className="dc-search-section-title text-lg font-bold">
        Search Results
      </h2>

      {!loading && movies.length > 0 && (
        <button
          onClick={() => {
            onClose();
            navigate("/recommend", { state: { search: query.trim() } });
          }}
          className="dc-search-personalized flex items-center gap-2 rounded-full px-4 py-2 text-xs font-medium transition"
        >
          <Sparkles size={15} />
          Personalized picks for "{query.trim()}"
        </button>
      )}
    </div>

    {loading ? (
      <div className="text-center text-gray-400 py-20">
        Searching...
      </div>
    ) : movies.length === 0 ? (
      <div className="text-center text-gray-400 py-20">
        No movies found
      </div>
    ) : (
      <div className="dc-search-results-grid grid gap-5">
        {movies.map((movie) => (
          <div key={movie.id} onClick={onClose} className="dc-search-result-item">
            <MovieCard movie={movie} />
          </div>
        ))}
      </div>
    )}
  </>
)}
</div>
</motion.div>
</motion.div>
</AnimatePresence>
  );
}