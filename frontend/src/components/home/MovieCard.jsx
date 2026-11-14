import { Play, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PosterImage from "../ui/PosterImage";

export default function MovieCard({ movie }) {
  const navigate = useNavigate();
  const year = movie.release_date ? new Date(movie.release_date).getFullYear() : "—";
  return (
    <article className="dc-movie-card" onClick={() => navigate(`/movie/${movie.id}`)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") navigate(`/movie/${movie.id}`); }} role="link" tabIndex={0} aria-label={`View ${movie.title}`}>
      <div className="dc-movie-poster">
        <PosterImage src={movie.poster_url} title={movie.title} className="dc-movie-poster-image" imgClassName="dc-movie-poster-image" />
        <span className="dc-movie-rating"><Star size={11} fill="currentColor" /> {movie.vote_average ? movie.vote_average.toFixed(1) : "NR"}</span>
        <span className="dc-movie-open"><Play size={17} fill="currentColor" /></span>
      </div>
      <div className="dc-movie-info">
        <h3>{movie.title}</h3>
        <span>{year}</span>
        {movie.recommendation_reason && (
          <p
            className="dc-movie-recommendation-reason"
            style={{
              margin: "6px 0 0",
              fontSize: "11px",
              lineHeight: 1.4,
              opacity: 0.78,
              maxWidth: "190px",
            }}
          >
            {movie.recommendation_reason}
          </p>
        )}
      </div>
    </article>
  );
}
