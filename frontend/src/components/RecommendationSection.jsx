import { useNavigate } from "react-router-dom";
import PosterImage from "./ui/PosterImage";

/**
 * Pure, reusable "row of recommended movies" section. Takes its data via
 * props instead of fetching internally, so it can back both the
 * personalized (content + genre affinity) and collaborative-filtering
 * ("viewers like you") rows without duplicating fetch logic or firing
 * the same network request twice.
 */
export default function RecommendationSection({
  movies = [],
  loading = false,
  title = "Recommended For You",
  eyebrow = "Your AI picks",
  description = "Explore movies chosen by your personalized recommendation engine.",
  emptyMessage = null,
}) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 mt-20">
        <div className="mb-6 h-6 w-56 animate-pulse rounded-full bg-white/10" />
        <div className="flex gap-6 overflow-x-hidden pb-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-[330px] w-[220px] shrink-0 animate-pulse rounded-[28px] bg-zinc-800"
            />
          ))}
        </div>
      </section>
    );
  }

  if (movies.length === 0) {
    if (!emptyMessage) return null;

    return (
      <section className="max-w-7xl mx-auto px-6 mt-20">
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-8 text-center text-sm text-slate-400">
          {emptyMessage}
        </div>
      </section>
    );
  }

  return (
    <section className="max-w-7xl mx-auto px-6 mt-20">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] text-purple-400 mb-2">
            {eyebrow}
          </p>
          <h2 className="text-3xl font-bold text-white">{title}</h2>
        </div>
        <p className="text-sm text-gray-400 max-w-xl">
          {description}
        </p>
      </div>

      <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide scroll-smooth">
        {movies.map((movie) => {
          const isUpcoming = Boolean(
            movie.release_date && new Date(movie.release_date) > new Date()
          );

          return (
          <div
            key={movie.id}
            onClick={() => navigate(`/movie/${movie.id}`)}
            className="group relative min-w-[220px] shrink-0 cursor-pointer overflow-hidden rounded-[28px] border border-cm-line bg-cm-surface shadow-[0_26px_80px_rgba(81,44,211,0.15)] transition duration-500 hover:-translate-y-2 hover:border-cm-purple/40 hover:shadow-[0_24px_80px_rgba(168,85,247,0.35)]"
          >
            <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-br from-cm-purple/20 via-transparent to-cm-cyan/10 opacity-70" />
            <PosterImage
              src={movie.poster_url}
              title={movie.title}
              className="h-[330px] w-full rounded-[28px]"
              imgClassName="h-[330px] w-full rounded-[28px] object-cover transition duration-500 group-hover:scale-110"
            />

            {isUpcoming && (
              <div className="absolute inset-x-3 top-12 z-30 flex justify-center">
                <div className="rounded-full bg-cm-purple-deep px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white shadow-lg">
                  Coming Soon
                </div>
              </div>
            )}

            <div className="absolute inset-x-3 top-3 z-30 flex items-center justify-between">
              <div className="rounded-full bg-black/70 px-3 py-1 text-xs font-semibold text-cm-amber backdrop-blur">
                ⭐ {movie.vote_average?.toFixed(1) ?? "N/A"}
              </div>
            </div>

            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-black via-black/70 to-transparent opacity-0 transition-all duration-300 group-hover:opacity-100">
              <div className="absolute bottom-0 w-full p-4">
                <h3 className="line-clamp-2 text-lg font-bold text-white">
                  {movie.title}
                </h3>
                <p className="mt-2 text-sm text-slate-300 line-clamp-2">
                  {movie.overview || "Curated just for your next watch."}
                </p>
              </div>
            </div>
          </div>
          );
        })}
      </div>
    </section>
  );
}
