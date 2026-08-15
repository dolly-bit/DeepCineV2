import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
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
  // e.g. { mode: "recommended", title: "Recommended For You" } - passed
  // straight through as router state to /movies. Omit to hide the "See
  // More" card.
  seeMoreState = null,
}) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 mt-14">
        <div className="mb-4 h-5 w-48 animate-pulse rounded-full bg-white/10" />
        <div className="flex gap-4 overflow-x-hidden pb-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-[250px] w-[180px] shrink-0 animate-pulse rounded-2xl bg-zinc-800"
            />
          ))}
        </div>
      </section>
    );
  }

  if (movies.length === 0) {
    if (!emptyMessage) return null;

    return (
      <section className="max-w-7xl mx-auto px-6 mt-14">
        <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-sm text-slate-400">
          {emptyMessage}
        </div>
      </section>
    );
  }

  return (
    <section className="max-w-7xl mx-auto px-6 mt-14">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-purple-400 mb-1">
            {eyebrow}
          </p>
          <h2 className="text-xl font-bold text-white">{title}</h2>
        </div>
        <p className="text-xs text-gray-400 max-w-xl">
          {description}
        </p>
      </div>

      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-cm-bg to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-cm-bg to-transparent" />

        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide scroll-smooth">
          {movies.map((movie) => {
            const isUpcoming = Boolean(
              movie.release_date && new Date(movie.release_date) > new Date()
            );

            return (
            <div
              key={movie.id}
              onClick={() => navigate(`/movie/${movie.id}`)}
              className="group relative min-w-[180px] shrink-0 cursor-pointer overflow-hidden rounded-2xl border border-cm-line bg-cm-surface shadow-[0_16px_50px_rgba(81,44,211,0.15)] transition duration-500 hover:-translate-y-1.5 hover:border-cm-purple/40 hover:shadow-[0_16px_50px_rgba(168,85,247,0.35)]"
            >
              <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-br from-cm-purple/20 via-transparent to-cm-cyan/10 opacity-70" />
              <PosterImage
                src={movie.poster_url}
                title={movie.title}
                className="h-[250px] w-full rounded-2xl"
                imgClassName="h-[250px] w-full rounded-2xl object-cover transition duration-500 group-hover:scale-110"
              />

              {isUpcoming && (
                <div className="absolute inset-x-2 top-9 z-30 flex justify-center">
                  <div className="rounded-full bg-cm-purple-deep px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white shadow-lg">
                    Coming Soon
                  </div>
                </div>
              )}

              <div className="absolute inset-x-2 top-2 z-30 flex items-center justify-between">
                <div className="rounded-full bg-black/70 px-2 py-0.5 text-[11px] font-semibold text-cm-amber backdrop-blur">
                  ⭐ {movie.vote_average?.toFixed(1) ?? "N/A"}
                </div>
              </div>

              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-black via-black/70 to-transparent opacity-0 transition-all duration-300 group-hover:opacity-100">
                <div className="absolute bottom-0 w-full p-3">
                  <h3 className="line-clamp-2 text-sm font-bold text-white">
                    {movie.title}
                  </h3>
                  <p className="mt-1 text-xs text-slate-300 line-clamp-2">
                    {movie.overview || "Curated just for your next watch."}
                  </p>
                </div>
              </div>
            </div>
            );
          })}

          {seeMoreState && (
            <button
              onClick={() => navigate("/movies", { state: seeMoreState })}
              className="flex h-[250px] w-[130px] shrink-0 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-cm-purple/40 bg-cm-purple/10 text-cm-purple transition hover:bg-cm-purple/20"
            >
              <ArrowRight size={22} />
              <span className="text-xs font-semibold">See More</span>
            </button>
          )}
        </div>
      </div>
    </section>
  );
}