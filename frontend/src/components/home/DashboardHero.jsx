import { useEffect, useState } from "react";
import { Play, Info } from "lucide-react";
import { useNavigate } from "react-router-dom";
import BackdropImage from "../ui/BackdropImage";

export default function DashboardHero({ movies = [] }) {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!movies.length) return;

    const interval = setInterval(() => {
      setCurrent((prev) => (prev + 1) % movies.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [movies]);

  if (!movies.length) {
    return (
      <section className="relative h-[75vh] overflow-hidden bg-cm-bg">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.28),_transparent_45%)]" />
        <div className="relative z-10 flex h-full items-center justify-center px-6">
          <div className="max-w-xl rounded-[28px] border border-cm-line bg-white/5 px-8 py-10 text-center backdrop-blur-xl">
            <p className="text-sm uppercase tracking-[0.3em] text-cm-purple">
              Now showing
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-white">
              Discover your next favorite movie
            </h1>
            <p className="mt-3 text-sm text-cm-muted">
              We're loading the featured picks now.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const movie = movies[current];

  return (
    <section className="relative h-[80vh] w-full overflow-hidden">
      <BackdropImage
        src={movie.backdrop_url}
        title={movie.title}
        className="absolute inset-0 h-full w-full object-cover"
      />

      <div className="absolute inset-0 bg-gradient-to-r from-cm-bg via-cm-bg/80 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-t from-cm-bg via-transparent to-transparent" />

      <div className="relative z-10 mx-auto flex h-full max-w-7xl items-center px-6 lg:px-10">
        <div className="max-w-2xl">
          <span className="mb-5 inline-block rounded-full bg-cm-purple-deep px-4 py-1 text-sm font-semibold text-white">
            FEATURED
          </span>

          <h1 className="text-5xl font-extrabold text-white md:text-7xl">
            {movie.title}
          </h1>

          <div className="mt-5 flex items-center gap-6 text-cm-muted">
            <span>⭐ {movie.vote_average?.toFixed(1) ?? "N/A"}</span>
            <span>📅 {movie.release_date || "TBA"}</span>
          </div>

          <p className="mt-6 line-clamp-4 text-lg leading-8 text-slate-300">
            {movie.overview}
          </p>

          <div className="mt-10 flex gap-4">
            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cm-purple-deep to-cm-purple px-7 py-4 font-semibold text-white transition hover:brightness-110"
            >
              <Play size={20} />
              Watch Now
            </button>

            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="flex items-center gap-2 rounded-xl bg-white/10 px-7 py-4 font-semibold text-white transition hover:bg-white/20"
            >
              <Info size={20} />
              More Info
            </button>
          </div>
        </div>
      </div>

      <div className="absolute bottom-8 left-1/2 flex -translate-x-1/2 gap-3">
        {movies.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrent(index)}
            className={`rounded-full transition-all duration-300 ${
              current === index
                ? "h-2 w-10 bg-cm-purple"
                : "h-2 w-2 bg-white/40"
            }`}
          />
        ))}
      </div>
    </section>
  );
}
