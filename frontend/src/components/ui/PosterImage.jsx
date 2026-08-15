import { useState } from "react";

/**
 * A movie poster that can never render as a broken image icon.
 *
 * Root cause of the "posters not visible" bug: some components fell back
 * to a raw TMDB `poster_path` (e.g. "/abc123.jpg") when `poster_url` was
 * missing - that's not a full URL, so the browser tried to load it
 * relative to the current site and 404'd. On top of that, movies with no
 * poster at all (TMDB sometimes returns poster_path: null) had no
 * fallback whatsoever.
 *
 * This component is now the single place poster URLs get resolved and
 * given a graceful fallback, used by every card/detail view in the app.
 */
export default function PosterImage({
  src,
  title,
  className = "",
  imgClassName = "h-full w-full object-cover",
}) {
  const [failed, setFailed] = useState(false);

  const showFallback = !src || failed;

  if (showFallback) {
    const initial = (title || "?").trim().charAt(0).toUpperCase();

    return (
      <div
        className={`flex items-center justify-center bg-gradient-to-br from-cm-purple-deep via-cm-surface-2 to-cm-bg-alt ${className}`}
      >
        <div className="flex flex-col items-center gap-2 px-4 text-center">
          <span className="text-4xl font-black text-white/25">
            {initial}
          </span>
          <span className="line-clamp-2 text-xs font-medium text-white/40">
            {title || "No poster available"}
          </span>
        </div>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={title || "Movie poster"}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`${imgClassName} ${className}`}
    />
  );
}
