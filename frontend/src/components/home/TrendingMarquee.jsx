import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function TrendingMarquee({ movies = [], loading }) {
  const navigate = useNavigate();
  return (
    <section id="trending" className="dc-trending-section">
      <div className="dc-trending-heading">
        <div><span className="dc-slider-eyebrow">WHAT PEOPLE ARE WATCHING</span><h2>In the current rotation<span>.</span></h2></div>
        <span className="dc-trending-count">{loading ? "UPDATING PICKS" : `${movies.length} FILMS TO EXPLORE`}</span>
      </div>
      {loading ? (
        <div className="dc-trending-track">{[...Array(6)].map((_, index) => <div key={index} className="dc-movie-skeleton" />)}</div>
      ) : movies.length ? (
        <div className="dc-trending-track">{movies.slice(0, 12).map((movie) => <MovieCard key={movie.id} movie={movie} />)}</div>
      ) : (
        <div className="dc-trending-empty">Trending titles are taking a moment to arrive. Please refresh in a little while.</div>
      )}
      <button className="dc-trending-more" onClick={() => navigate("/login")}>Sign in to explore your picks <ArrowRight size={14} /></button>
    </section>
  );
}
