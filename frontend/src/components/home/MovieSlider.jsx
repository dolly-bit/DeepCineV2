import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, ArrowRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function MovieSlider({ title = "Movies", movies = [], loading, seeMoreState = null }) {
  const navigate = useNavigate();
  const sliderRef = useRef(null);
  const scroll = (direction) => sliderRef.current?.scrollBy({ left: direction * 680, behavior: "smooth" });

  return (
    <section className="dc-slider-section">
      <div className="dc-slider-heading">
        <div><span className="dc-slider-eyebrow">THE COLLECTION</span><h2>{title}</h2></div>
        <div className="dc-slider-controls">
          {seeMoreState && <button className="dc-view-all" onClick={() => navigate("/movies", { state: seeMoreState })}>View all <ArrowRight size={14} /></button>}
          <button aria-label="Scroll left" onClick={() => scroll(-1)}><ChevronLeft size={17} /></button>
          <button aria-label="Scroll right" onClick={() => scroll(1)}><ChevronRight size={17} /></button>
        </div>
      </div>
      <div ref={sliderRef} className="dc-slider-track">
        {loading ? [...Array(6)].map((_, index) => <div key={index} className="dc-movie-skeleton" />) :
          movies.length ? movies.map((movie) => <MovieCard key={movie.id} movie={movie} />) :
          <div className="dc-slider-empty">No films to show here just yet.</div>}
      </div>
    </section>
  );
}
