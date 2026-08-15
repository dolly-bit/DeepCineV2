import { useState } from "react";

/**
 * Same idea as PosterImage but for wide hero/backdrop images - falls
 * back to a themed gradient instead of a broken image icon when a
 * backdrop_url is missing or fails to load.
 */
export default function BackdropImage({ src, title, className = "" }) {
  const [failed, setFailed] = useState(false);

  const showFallback = !src || failed;

  if (showFallback) {
    return (
      <div
        className={`bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.35),_transparent_55%),radial-gradient(circle_at_bottom_right,_rgba(34,211,238,0.2),_transparent_50%)] bg-cm-bg ${className}`}
      />
    );
  }

  return (
    <img
      src={src}
      alt={title || "Movie backdrop"}
      loading="lazy"
      onError={() => setFailed(true)}
      className={className}
    />
  );
}
