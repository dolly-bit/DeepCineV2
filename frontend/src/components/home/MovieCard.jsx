import { Play, Info, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PosterImage from "../ui/PosterImage";

export default function MovieCard({ movie }) {
  const navigate = useNavigate();

  // TMDB's trending list genuinely can (and often does) include movies
  // that haven't released yet - pre-release buzz, trailer drops, and
  // festival premieres all move the needle. That's correct data, not a
  // bug, so instead of hiding it, we label it clearly.
  const isUpcoming = Boolean(
    movie.release_date && new Date(movie.release_date) > new Date()
  );

  return (
    <div className="group/card relative w-full max-w-[240px] flex-shrink-0 transition-all duration-300 hover:z-50">
      <div className="relative overflow-hidden rounded-3xl border border-cm-line bg-cm-surface shadow-[0_20px_60px_rgba(8,7,12,0.5)] transition-all duration-500 group-hover/card:-translate-y-3 group-hover/card:scale-105 group-hover/card:shadow-[0_24px_80px_rgba(168,85,247,0.35)]">
        <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-br from-cm-purple/20 via-transparent to-cm-cyan/10 opacity-70" />

        <PosterImage
          src={movie.poster_url}
          title={movie.title}
          className="h-[330px] w-full"
          imgClassName="h-[330px] w-full object-cover transition duration-500 group-hover/card:scale-110"
        />

        {isUpcoming && (
          <div className="absolute inset-x-3 top-14 z-30 flex justify-center">
            <div className="rounded-full bg-cm-purple-deep px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white shadow-lg">
              Coming Soon
            </div>
          </div>
        )}

        <div className="absolute inset-x-3 top-3 z-30 flex items-center justify-between">
          <div className="flex items-center gap-1 rounded-full bg-black/70 px-3 py-1 backdrop-blur">
            <Star size={14} fill="var(--color-cm-amber)" className="text-cm-amber" />
            <span className="text-sm font-semibold text-white">
              {movie.vote_average ? movie.vote_average.toFixed(1) : "N/A"}
            </span>
          </div>
          <div className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-slate-200 backdrop-blur">
            {movie.release_date
              ? new Date(movie.release_date).getFullYear()
              : "N/A"}
          </div>
        </div>

        <div className="absolute inset-0 z-20 bg-gradient-to-t from-black via-black/70 to-transparent opacity-0 transition-all duration-300 group-hover/card:opacity-100">
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-cm-purple-deep to-cm-purple shadow-lg shadow-cm-purple/30 transition hover:scale-110"
            >
              <Play fill="white" className="ml-1 text-white" />
            </button>
          </div>

          <div className="absolute bottom-0 w-full p-4">
            <h3 className="line-clamp-2 text-lg font-bold text-white">
              {movie.title}
            </h3>
            <p className="mt-2 text-sm text-slate-300">
              {movie.overview?.slice(0, 80) || "A cinematic pick curated for your vibe."}
            </p>

            <button
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-white/10 py-2 text-white transition hover:bg-white/20"
            >
              <Info size={18} />
              More Info
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
