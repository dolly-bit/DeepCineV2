import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, ArrowRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function MovieSlider({
  title = "Movies",
  movies = [],
  loading,
  // e.g. { mode: "trending", title: "Trending Movies" } - passed straight
  // through as router state to /movies, which already knows how to load
  // each mode. Omit to hide the "See More" card.
  seeMoreState = null,
}) {
  const navigate = useNavigate();
  const sliderRef = useRef(null);

  const scrollLeft = () => {
    sliderRef.current?.scrollBy({
      left: 700,
      behavior: "smooth",
    });
  };

  const scrollRight = () => {
    sliderRef.current?.scrollBy({
      left: -700,
      behavior: "smooth",
    });
  };

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-6">
        <h2 className="text-xl font-bold text-white mb-4">{title}</h2>

        <div className="flex gap-4 overflow-x-hidden">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-[250px] w-[180px] shrink-0 rounded-2xl bg-zinc-800 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="max-w-7xl mx-auto px-6 lg:px-10 py-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-white">{title}</h2>
        <div className="flex gap-1.5">
          <button
            onClick={scrollLeft}
            aria-label="Scroll left"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-900/90 border border-white/10 text-white shadow-lg hover:bg-purple-600 transition"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={scrollRight}
            aria-label="Scroll right"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-900/90 border border-white/10 text-white shadow-lg hover:bg-purple-600 transition"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="relative">
        {/* Fade edges hint that the row scrolls, instead of cards just
            looking abruptly cut off at the container boundary. */}
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-cm-bg to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-cm-bg to-transparent" />

        <div
          ref={sliderRef}
          className="flex gap-4 overflow-x-auto scroll-smooth scrollbar-hide pb-2"
        >
          {movies.length === 0 ? (
            <div className="w-full rounded-2xl border border-dashed border-white/10 bg-white/5 px-6 py-8 text-sm text-slate-400">
              No movies available right now.
            </div>
          ) : (
            <>
              {movies.map((movie) => (
                <div
                  key={movie.id}
                  className="flex-shrink-0 cursor-pointer"
                  onClick={() => navigate(`/movie/${movie.id}`)}
                >
                  <MovieCard movie={movie} />
                </div>
              ))}

              {seeMoreState && (
                <button
                  onClick={() => navigate("/movies", { state: seeMoreState })}
                  className="flex h-[250px] w-[130px] shrink-0 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-cm-purple/40 bg-cm-purple/10 text-cm-purple transition hover:bg-cm-purple/20"
                >
                  <ArrowRight size={22} />
                  <span className="text-xs font-semibold">See More</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}