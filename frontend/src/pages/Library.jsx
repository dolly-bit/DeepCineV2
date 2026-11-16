import { useEffect, useMemo, useState } from "react";
import { Bookmark, Heart, LoaderCircle, Star } from "lucide-react";
import HomeSidebar from "../components/layout/HomeSidebar";
import Navbar from "../components/layout/Navbar";
import MovieCard from "../components/home/MovieCard";
import { getMyRatings, getWatchlist, getMovieDetails } from "../services/movies";

export default function Library() {
  const [section, setSection] = useState("collection");
  const [watchlist, setWatchlist] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [favoriteMovies, setFavoriteMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadLibrary() {
      setLoading(true);
      setError("");
      try {
        const [saved, rated] = await Promise.all([getWatchlist(), getMyRatings()]);
        if (cancelled) return;
        setWatchlist(saved || []);
        setRatings(rated || []);
        const favorites = (rated || []).filter((item) => Number(item.rating) >= 4);
        const details = await Promise.all(
          favorites.map((item) => getMovieDetails(item.tmdb_id).catch(() => null))
        );
        if (!cancelled) setFavoriteMovies(details.filter(Boolean));
      } catch (err) {
        console.error("Could not load library", err);
        if (!cancelled) setError("Your library couldn't be loaded. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadLibrary();
    return () => { cancelled = true; };
  }, []);

  const collectionMovies = useMemo(() => watchlist.map((item) => ({
    id: item.tmdb_id,
    tmdb_id: item.tmdb_id,
    title: item.title,
    poster_url: item.poster_url,
    overview: "Saved to your personal collection.",
  })), [watchlist]);

  const activeMovies = section === "collection" ? collectionMovies : favoriteMovies;
  const favoriteCount = ratings.filter((item) => Number(item.rating) >= 4).length;

  return (
    <div className="dc-app-shell">
      <HomeSidebar />
      <main className="dc-app-main">
        <Navbar />
        <section className="dc-library-page">
          <div className="dc-library-heading">
            <span className="dc-slider-eyebrow">YOUR PERSONAL CINEMA</span>
            <h1>My Library</h1>
            <p>Everything you've saved and the films you've loved, in one place.</p>
          </div>
          <div className="dc-library-tabs" role="tablist" aria-label="Library sections">
            <button type="button" role="tab" aria-selected={section === "collection"} className={section === "collection" ? "active" : ""} onClick={() => setSection("collection")}>
              <Bookmark size={16}/> My Collection <span>{watchlist.length}</span>
            </button>
            <button type="button" role="tab" aria-selected={section === "favorites"} className={section === "favorites" ? "active" : ""} onClick={() => setSection("favorites")}>
              <Heart size={16}/> Favourites <span>{favoriteCount}</span>
            </button>
          </div>
          {loading ? (
            <div className="dc-library-loading"><LoaderCircle className="animate-spin" size={22}/> Loading your library...</div>
          ) : error ? (
            <p className="dc-library-empty">{error}</p>
          ) : activeMovies.length ? (
            <div className="dc-library-grid">{activeMovies.map((movie) => <MovieCard key={movie.id} movie={movie}/>)}</div>
          ) : (
            <div className="dc-library-empty-state">
              {section === "collection" ? <Bookmark size={28}/> : <Star size={28}/>}
              <h2>{section === "collection" ? "Your collection is empty" : "No favourites yet"}</h2>
              <p>{section === "collection" ? "Add films to My List from any movie details page." : "Rate films 4 or 5 stars and they'll appear here."}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
