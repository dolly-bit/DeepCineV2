import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function TrendingMovies({
  title = "Trending Movies",
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
        <h2 className="text-3xl font-bold text-white mb-6">
          {title}
        </h2>

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

  if (!movies.length) {
    return (
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-8">
        <h2 className="text-3xl font-bold text-white mb-6">
          {title}
        </h2>

        <p className="text-gray-400">
          No movies available.
        </p>
      </section>
    );
  }

  return (
    <section className="max-w-7xl mx-auto px-6 lg:px-10 py-8">
      <h2 className="text-3xl font-bold text-white mb-6">
        {title}
      </h2>

      <div className="relative group">

        {/* Left Button */}
        <button
          onClick={scrollLeft}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-black/70 hover:bg-red-600 transition-all duration-300 p-3 rounded-full shadow-lg opacity-0 group-hover:opacity-100"
        >
          <ChevronLeft size={26} className="text-white" />
        </button>

        {/* Movies */}
        <div
          ref={sliderRef}
          className="flex gap-6 overflow-x-auto scroll-smooth scrollbar-hide"
        >
          {movies.map((movie) => (
            <div
              key={movie.id}
              className="flex-shrink-0 cursor-pointer"
              onClick={() => navigate(`/movie/${movie.id}`)}
            >
              <MovieCard movie={movie} />
            </div>
          ))}
        </div>

        {/* Right Button */}
        <button
          onClick={scrollRight}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-black/70 hover:bg-red-600 transition-all duration-300 p-3 rounded-full shadow-lg opacity-0 group-hover:opacity-100"
        >
          <ChevronRight size={26} className="text-white" />
        </button>

      </div>
    </section>
  );
}