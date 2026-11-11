import { useEffect, useState } from "react";
import { ArrowUpRight, Play, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import BackdropImage from "../ui/BackdropImage";

export default function DashboardHero({ movies = [] }) {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (movies.length < 2) return undefined;
    const interval = window.setInterval(() => setCurrent((value) => (value + 1) % movies.length), 6500);
    return () => window.clearInterval(interval);
  }, [movies.length]);

  if (!movies.length) {
    return <section className="dc-dashboard-hero dc-dashboard-empty"><div><span className="dc-landing-kicker"><Sparkles size={14} /> YOUR PERSONAL SCREENING ROOM</span><h1>Tonight deserves<br /><em>a better story.</em></h1><p>We're bringing your featured films into focus. Explore the catalogue while they load.</p><button onClick={() => navigate("/discover")}>Explore films <ArrowUpRight size={16} /></button></div></section>;
  }

  const movie = movies[current % movies.length];
  return (
    <section className="dc-dashboard-hero">
      <BackdropImage src={movie.backdrop_url || movie.poster_url} title={movie.title} className="dc-dashboard-image" />
      <div className="dc-dashboard-overlay" />
      <div className="dc-dashboard-content">
        <span className="dc-landing-kicker"><Sparkles size={14} /> YOUR PERSONAL SCREENING ROOM</span>
        <p className="dc-dashboard-label">FEATURED FILM <span> / {String(current + 1).padStart(2, "0")}</span></p>
        <h1>{movie.title}</h1>
        <div className="dc-dashboard-meta"><span>★ {movie.vote_average?.toFixed?.(1) ?? "—"}</span><span>{movie.release_date?.slice(0, 4) || "Release date unavailable"}</span></div>
        <p className="dc-dashboard-overview">{movie.overview || "A new story is waiting to be discovered."}</p>
        <div className="dc-dashboard-actions"><button onClick={() => navigate(`/movie/${movie.id}`)}><Play size={15} fill="currentColor" /> Explore film</button><button className="dc-dashboard-secondary" onClick={() => navigate("/discover")}>Browse catalogue <ArrowUpRight size={15} /></button></div>
      </div>
      <div className="dc-dashboard-pagination">{movies.slice(0, 6).map((item, index) => <button key={item.id} aria-label={`Show ${item.title}`} onClick={() => setCurrent(index)} className={index === current ? "active" : ""} />)}</div>
    </section>
  );
}
