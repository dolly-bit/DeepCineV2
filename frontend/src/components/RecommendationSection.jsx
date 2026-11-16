import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import MovieCard from "./home/MovieCard";

export default function RecommendationSection({
  movies = [],
  loading = false,
  title = "Recommended For You",
  eyebrow = "Your AI picks",
  description = "",
  emptyMessage = null,
  seeMoreState = null,
}) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <section className="dc-slider-section dc-recommendation-section">
        <div className="dc-slider-heading"><div><span className="dc-slider-eyebrow">{eyebrow}</span><h2>{title}</h2></div></div>
        <div className="dc-slider-track">{Array.from({ length: 7 }).map((_, index) => <div key={index} className="dc-movie-skeleton" />)}</div>
      </section>
    );
  }

  if (!movies.length) {
    if (!emptyMessage) return null;
    return <section className="dc-recommendation-empty"><span className="dc-slider-eyebrow">{eyebrow}</span><h2>{title}</h2><p>{emptyMessage}</p></section>;
  }

  return (
    <section className="dc-slider-section dc-recommendation-section">
      <div className="dc-slider-heading">
        <div><span className="dc-slider-eyebrow">{eyebrow}</span><h2>{title}</h2>{description && <p className="dc-recommendation-description">{description}</p>}</div>
        <div className="dc-slider-controls">{seeMoreState && <button className="dc-view-all" onClick={() => navigate("/movies", { state: seeMoreState })}>View all <ArrowRight size={14} /></button>}</div>
      </div>
      <div className="dc-slider-track">{movies.map((movie) => <MovieCard key={movie.id} movie={movie} />)}</div>
    </section>
  );
}
