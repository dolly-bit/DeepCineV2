import { useMemo, useState } from "react";
import { ArrowRight, Search, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { searchMovies, recordSearch } from "../../services/movies";

export default function Hero({ movies = [] }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const featured = useMemo(() => movies.find((movie) => movie.backdrop_url || movie.poster_url) || movies[0], [movies]);
  const image = featured?.backdrop_url || featured?.poster_url || "https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg";

  const handleSearch = async (event) => {
    event.preventDefault();
    if (!query.trim() || searching) return;
    setSearching(true);
    recordSearch(query.trim());
    try {
      const results = await searchMovies(query.trim());
      navigate("/recommend", { state: { search: query.trim(), movies: results } });
    } catch (error) {
      console.error("Movie search failed:", error);
    } finally {
      setSearching(false);
    }
  };

  return (
    <section className="dc-landing">
      <div className="dc-landing-backdrop" style={{ backgroundImage: `url("${image}")` }} />
      <div className="dc-landing-shade" />
      <div className="dc-landing-inner">
        <div>
          <div className="dc-landing-kicker"><Sparkles size={14} /> A PERSONAL CINEMA COMPANION</div>
          <h1 className="dc-landing-title">Your taste.<br />Your <em>next film.</em></h1>
          <p className="dc-landing-copy">Stop searching through endless lists. Discover films through your taste, explore new moods, and keep every great find in one place.</p>
          <form className="dc-searchbar" onSubmit={handleSearch}>
            <Search size={17} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a film, actor or genre…" aria-label="Search movies" />
            <button type="submit" disabled={searching}>{searching ? "Searching…" : <>Find a film <ArrowRight size={15} /></>}</button>
          </form>
          <div className="dc-landing-actions"><Link to="/signup">Build your watchlist <ArrowRight size={14} /></Link><Link to="/login">Already a member? Sign in</Link></div>
        </div>
        {featured && <aside className="dc-feature-card">
          <img src={featured.poster_url || image} alt={featured.title || "Featured film"} />
          <div className="dc-feature-caption"><span>IN THE SPOTLIGHT</span><strong>{featured.vote_average ? `★ ${featured.vote_average.toFixed(1)} / 10` : "FEATURED PICK"}</strong></div>
        </aside>}
      </div>
    </section>
  );
}
