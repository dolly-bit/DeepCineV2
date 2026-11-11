import { useEffect, useState } from "react";
import { ArrowUpRight, Info, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";
import BackdropImage from "../ui/BackdropImage";

export default function DashboardHero({ movies = [] }) {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (movies.length < 2) return undefined;
    const interval = window.setInterval(() => setCurrent((value) => (value + 1) % Math.min(movies.length, 8)), 8000);
    return () => window.clearInterval(interval);
  }, [movies.length]);

  if (!movies.length) {
    return (
      <section className="dc-feature-hero dc-feature-hero-empty">
        <div className="dc-feature-shade" />
        <div className="dc-feature-copy">
          <span className="dc-feature-kicker">YOUR NEXT FAVORITE FILM IS WAITING</span>
          <h1>Find your<br />next <em>story.</em></h1>
          <p>Explore a catalogue of films and let DeepCine help you find what to watch next.</p>
          <button className="dc-hero-primary" onClick={() => navigate("/discover")}><Play size={16} fill="currentColor" /> Explore movies</button>
        </div>
      </section>
    );
  }

  const movie = movies[current % movies.length];
  const year = movie.release_date ? movie.release_date.slice(0, 4) : null;
  return (
    <section className="dc-feature-hero">
      <BackdropImage src={movie.backdrop_url || movie.poster_url} title={movie.title} className="dc-feature-backdrop" />
      <div className="dc-feature-shade" />
      <div className="dc-feature-copy" key={movie.id}>
        <span className="dc-feature-kicker">DEEPCINE PRESENTS <i /> FEATURED FILM</span>
        <h1>{movie.title}</h1>
        <div className="dc-feature-meta">
          {movie.vote_average ? <span className="dc-feature-rating">★ {movie.vote_average.toFixed(1)} / 10</span> : null}
          {year && <span>{year}</span>}
          <span>Film</span>
        </div>
        <p>{movie.overview || "A story worth discovering. Explore the film to see more details."}</p>
        <div className="dc-feature-actions">
          <button className="dc-hero-primary" onClick={() => navigate(`/movie/${movie.id}`)}><Play size={17} fill="currentColor" /> Explore film</button>
          <button className="dc-hero-secondary" onClick={() => navigate(`/movie/${movie.id}`)}><Info size={17} /> More Info</button>
        </div>
      </div>
      <div className="dc-feature-pagination" aria-label="Featured films">
        {movies.slice(0, 8).map((item, index) => (
          <button key={item.id} type="button" aria-label={`Show ${item.title}`} onClick={() => setCurrent(index)} className={index === current ? "active" : ""} />
        ))}
      </div>
      <button className="dc-feature-discover" onClick={() => navigate("/discover")}>Explore catalogue <ArrowUpRight size={15} /></button>
    </section>
  );
}
