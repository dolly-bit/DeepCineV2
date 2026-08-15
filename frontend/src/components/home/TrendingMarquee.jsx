import { useNavigate } from "react-router-dom";
import MovieCard from "./MovieCard";

export default function TrendingMarquee({ movies = [], loading }) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 lg:px-10 pt-2 pb-6">
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
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-10 text-center text-gray-400">
        No trending movies available.
      </section>
    );
  }

  const loop = [...movies, ...movies];

  return (
    <section
      id="trending"
      className="max-w-7xl mx-auto px-6 lg:px-10 pt-2 pb-6 overflow-hidden"
    >
      <div className="relative overflow-hidden">
        <div className="flex gap-6 animate-marquee w-max">
          {loop.map((movie, index) => (
            <div
              key={`${movie.id}-${index}`}
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="cursor-pointer"
            >
              <MovieCard movie={movie} />
            </div>
          ))}
        </div>

        <div className="absolute left-0 top-0 h-full w-24 bg-gradient-to-r from-[#08070C] to-transparent pointer-events-none" />
        <div className="absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-[#08070C] to-transparent pointer-events-none" />
      </div>
    </section>
  );
}