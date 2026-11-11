import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, ChevronLeft, ChevronRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function TrendingMarquee({ movies = [], loading }) {
  const navigate = useNavigate();
  const trackRef = useRef(null);
  const [paused, setPaused] = useState(false);

  const move = useCallback((direction) => {
    const track = trackRef.current;
    if (!track) return;
    const card = track.querySelector(".dc-movie-card");
    const distance = card ? card.getBoundingClientRect().width + 16 : 180;
    const atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - distance;
    if (direction > 0 && atEnd) {
      track.scrollTo({ left: 0, behavior: "smooth" });
    } else {
      track.scrollBy({ left: direction * distance, behavior: "smooth" });
    }
  }, []);

  useEffect(() => {
    if (loading || movies.length < 2 || paused) return undefined;
    const timer = window.setInterval(() => move(1), 3500);
    return () => window.clearInterval(timer);
  }, [loading, movies.length, paused, move]);

  return (
    <section id="trending" className="dc-trending-section">
      <div className="dc-trending-heading">
        <div><span className="dc-slider-eyebrow">WHAT PEOPLE ARE WATCHING</span><h2>Trending films<span>.</span></h2></div>
        <div className="dc-trending-tools">
          <span className="dc-trending-count">{loading ? "UPDATING PICKS" : `${movies.length} FILMS TO EXPLORE`}</span>
          <button type="button" aria-label="Previous movies" onClick={() => move(-1)}><ChevronLeft size={17}/></button>
          <button type="button" aria-label="Next movies" onClick={() => move(1)}><ChevronRight size={17}/></button>
        </div>
      </div>
      {loading ? (
        <div className="dc-trending-track">{[...Array(6)].map((_, index) => <div key={index} className="dc-movie-skeleton" />)}</div>
      ) : movies.length ? (
        <div
          ref={trackRef}
          className="dc-trending-track dc-trending-carousel"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          onFocusCapture={() => setPaused(true)}
          onBlurCapture={() => setPaused(false)}
        >
          {movies.slice(0, 12).map((movie) => <MovieCard key={movie.id} movie={movie} />)}
        </div>
      ) : (
        <div className="dc-trending-empty">Trending titles are taking a moment to arrive. Please refresh in a little while.</div>
      )}
      <button className="dc-trending-more" onClick={() => navigate("/discover")}>Find new movies <ArrowRight size={14} /></button>
    </section>
  );
}
