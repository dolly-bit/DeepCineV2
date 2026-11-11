import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import DashboardHero from "../components/home/DashboardHero";
import MovieSlider from "../components/home/MovieSlider";
import PersonalizedMovies from "../components/PersonalizedMovies";
import CollaborativeMovies from "../components/CollaborativeMovies";
import MoodBrowser from "../components/home/MoodBrowser";
import { getTrendingMovies, getTopRatedMovies, getUpcomingMovies } from "../services/movies";

function filterFutureMovies(movies) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return movies.filter((movie) => {
    if (!movie.release_date) return false;
    const releaseDate = new Date(movie.release_date);
    return !Number.isNaN(releaseDate.getTime()) && releaseDate >= today;
  }).sort((a, b) => new Date(a.release_date) - new Date(b.release_date));
}

export default function Home() {
  const [trending, setTrending] = useState([]);
  const [topRated, setTopRated] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getTrendingMovies(), getTopRatedMovies(), getUpcomingMovies()])
      .then(([trend, top, up]) => {
        if (cancelled) return;
        setTrending(trend || []);
        setTopRated(top || []);
        setUpcoming(filterFutureMovies(up || []));
      })
      .catch((error) => {
        console.error("Failed to load home catalogue:", error);
        if (!cancelled) {
          setTrending([]);
          setTopRated([]);
          setUpcoming([]);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <main className="dc-home">
      <Navbar />
      <DashboardHero movies={trending} />
      <div className="dc-home-content">
        <section className="dc-home-rail" id="trending">
          <MovieSlider title="Trending Now" movies={trending} loading={loading} seeMoreState={{ mode: "trending", title: "Trending Now" }} />
        </section>
        <MoodBrowser />
        <PersonalizedMovies />
        <CollaborativeMovies />
        <MovieSlider title="Top Rated Films" movies={topRated} loading={loading} seeMoreState={{ mode: "top-rated", title: "Top Rated Films" }} />
        <MovieSlider title="Coming Soon" movies={upcoming} loading={loading} seeMoreState={{ mode: "upcoming", title: "Coming Soon" }} />
      </div>
      <footer className="dc-home-footer"><span>DEEPCINE</span><span>DISCOVER SOMETHING WORTH WATCHING.</span></footer>
    </main>
  );
}
