import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function MovieSlider({
  title = "Movies",
  movies = [],
  loading,
}) {
  const navigate = useNavigate();
  const sliderRef = useRef(null);

  const scrollLeft = () => {
    sliderRef.current?.scrollBy({
      left: -900,
      behavior: "smooth",
    });
  };

  const scrollRight = () => {
    sliderRef.current?.scrollBy({
      left: 900,
      behavior: "smooth",
    });
  };

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-8">
        <h2 className="text-3xl font-bold text-white mb-6">{title}</h2>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-[330px] rounded-2xl bg-zinc-800 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="max-w-7xl mx-auto px-6 lg:px-10 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h2 className="text-3xl font-bold text-white">{title}</h2>
        <div className="flex gap-2">
          <button
            onClick={scrollLeft}
            className="w-11 h-11 rounded-full bg-zinc-900/90 border border-white/10 text-white shadow-lg hover:bg-purple-600 transition"
          >
            <ChevronLeft />
          </button>
          <button
            onClick={scrollRight}
            className="w-11 h-11 rounded-full bg-zinc-900/90 border border-white/10 text-white shadow-lg hover:bg-purple-600 transition"
          >
            <ChevronRight />
          </button>
        </div>
      </div>

      <div className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#08070C]/60 p-4">
        <div
          ref={sliderRef}
          className="flex gap-6 overflow-x-auto scroll-smooth scrollbar-hide pb-2"
        >
          {movies.length === 0 ? (
            <div className="w-full rounded-2xl border border-dashed border-white/10 bg-white/5 px-6 py-8 text-sm text-slate-400">
              No movies available right now.
            </div>
          ) : (
            movies.map((movie) => (
              <div
                key={movie.id}
                className="flex-shrink-0 cursor-pointer"
                onClick={() => navigate(`/movie/${movie.id}`)}
              >
                <MovieCard movie={movie} />
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}