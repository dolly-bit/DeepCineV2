import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, LoaderCircle } from "lucide-react";
import HomeSidebar from "../components/layout/HomeSidebar";
import Navbar from "../components/layout/Navbar";
import MovieCard from "../components/home/MovieCard";
import { getMovieDetails, getSimilarMovies } from "../services/movies";

export default function SimilarMoviesPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [movies, setMovies] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [movieData, similarData] = await Promise.all([
          getMovieDetails(id),
          getSimilarMovies(id, 1),
        ]);
        if (cancelled) return;
        setMovie(movieData);
        setMovies(similarData.results);
        setPage(similarData.page);
        setTotalPages(similarData.total_pages);
      } catch (err) {
        console.error("Could not load similar movies", err);
        if (!cancelled) setError("Similar movies could not be loaded. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [id]);

  async function loadMore() {
    if (loadingMore || page >= totalPages) return;
    setLoadingMore(true);
    setError("");
    try {
      const next = await getSimilarMovies(id, page + 1);
      setMovies((current) => {
        const known = new Set(current.map((item) => item.id));
        return [...current, ...next.results.filter((item) => !known.has(item.id))];
      });
      setPage(next.page);
      setTotalPages(next.total_pages);
    } catch (err) {
      console.error("Could not load another page of similar movies", err);
      setError("More movies could not be loaded. Please retry.");
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <div className="dc-app-shell">
      <HomeSidebar />
      <main className="dc-app-main">
        <Navbar />
        <section className="dc-similar-page">
          <button type="button" className="dc-similar-back" onClick={() => navigate(`/movie/${id}`)}>
            <ArrowLeft size={16} /> Back to movie
          </button>
          <span className="dc-slider-eyebrow">EXPLORE THE COLLECTION</span>
          <h1>More films like {movie?.title || "this movie"}</h1>
          <p className="dc-similar-intro">Discover more titles with similar themes and genres. Recommendations are supplied by TMDB's similar-movies catalogue.</p>
          {loading ? (
            <div className="dc-similar-loading"><LoaderCircle className="animate-spin" /> Loading similar movies...</div>
          ) : movies.length ? (
            <>
              <div className="dc-similar-grid">
                {movies.map((item) => <MovieCard key={item.id} movie={item} />)}
              </div>
              {error && <p className="dc-similar-error" role="alert">{error}</p>}
              {page < totalPages ? (
                <div className="dc-similar-load-wrap">
                  <button type="button" className="dc-similar-load" onClick={loadMore} disabled={loadingMore}>
                    {loadingMore ? <><LoaderCircle size={16} className="animate-spin" /> Loading...</> : "Load more movies"}
                  </button>
                  <span>Page {page} of {totalPages}</span>
                </div>
              ) : <p className="dc-similar-end">You've reached the end of this collection.</p>}
            </>
          ) : (
            <p className="dc-similar-empty">{error || "No similar movies are available for this title yet."}</p>
          )}
        </section>
      </main>
    </div>
  );
}
