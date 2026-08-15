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
      <section className="relative h-[52vh] overflow-hidden bg-cm-bg">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.28),_transparent_45%)]" />
        <div className="relative z-10 flex h-full items-center justify-center px-6">
          <div className="max-w-lg rounded-3xl border border-cm-line bg-white/5 px-7 py-8 text-center backdrop-blur-xl">
            <p className="text-xs uppercase tracking-[0.3em] text-cm-purple">
              Now showing
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              Discover your next favorite movie
            </h1>
            <p className="mt-2 text-sm text-cm-muted">
              We're loading the featured picks now.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const movie = movies[current];

  return (
    <section className="relative h-[66vh] w-full overflow-hidden">
      <BackdropImage
        src={movie.backdrop_url}
        title={movie.title}
        className="absolute inset-0 h-full w-full object-cover"
      />

      <div className="absolute inset-0 bg-gradient-to-r from-cm-bg via-cm-bg/80 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-t from-cm-bg via-transparent to-transparent" />

      <div className="relative z-10 mx-auto flex h-full max-w-7xl items-center px-6 lg:px-10">
        <div className="max-w-xl">
          <span className="mb-3 inline-block rounded-full bg-cm-purple-deep px-3 py-1 text-xs font-semibold text-white">
            FEATURED
          </span>

          <h1 className="text-3xl font-extrabold text-white md:text-5xl">
            {movie.title}
          </h1>

          <div className="mt-3 flex items-center gap-5 text-sm text-cm-muted">
            <span>⭐ {movie.vote_average?.toFixed(1) ?? "N/A"}</span>
            <span>📅 {movie.release_date || "TBA"}</span>
          </div>

          <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-300 md:text-base">
            {movie.overview}
          </p>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cm-purple-deep to-cm-purple px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110"
            >
              <Play size={16} />
              Watch Now
            </button>

            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="flex items-center gap-2 rounded-xl bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
            >
              <Info size={16} />
              More Info
            </button>
          </div>
        </div>
      </div>

      <div className="absolute bottom-5 left-1/2 flex -translate-x-1/2 gap-2">
        {movies.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrent(index)}
            className={`rounded-full transition-all duration-300 ${
              current === index
                ? "h-1.5 w-7 bg-cm-purple"
                : "h-1.5 w-1.5 bg-white/40"
            }`}
          />
        ))}
      </div>
    </section>
  );
}
