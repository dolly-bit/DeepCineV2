import { useEffect, useState } from "react";
import { Sparkles, Users, History, Search } from "lucide-react";

import Navbar from "../components/layout/Navbar";
import DashboardHero from "../components/home/DashboardHero";
import MovieSlider from "../components/home/MovieSlider";
import PersonalizedMovies from "../components/PersonalizedMovies";
import CollaborativeMovies from "../components/CollaborativeMovies";
import MoodBrowser from "../components/home/MoodBrowser";
import { getAuthState } from "../services/auth";

import {
  getTrendingMovies,
  getTopRatedMovies,
  getUpcomingMovies,
} from "../services/movies";

const HOW_IT_WORKS = [
  {
    icon: Sparkles,
    title: "Personalized for you",
    description:
      "Genre-affinity + content matching learns what you love from every movie you open.",
  },
  {
    icon: Users,
    title: "Collaborative filtering",
    description:
      "An ALS matrix-factorization model matches you with viewers who share your actual watch patterns.",
  },
  {
    icon: History,
    title: "Learns from your history",
    description:
      "Every movie you view is logged to your watch history, sharpening your recommendations over time.",
  },
  {
    icon: Search,
    title: "Search-aware",
    description:
      "What you search for feeds straight back into your recommendation engine.",
  },
];

function filterFutureMovies(movies) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return movies
    .filter((movie) => {
      if (!movie.release_date) return false;
      const releaseDate = new Date(movie.release_date);
      return !Number.isNaN(releaseDate.getTime()) && releaseDate >= today;
    })
    .sort((a, b) => new Date(a.release_date) - new Date(b.release_date));
}

export default function Home() {
  const [trending, setTrending] = useState([]);
  const [topRated, setTopRated] = useState([]);
  const [upcoming, setUpcoming] = useState([]);

  const [loading, setLoading] = useState(true);

  const { userId } = getAuthState();

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      getTrendingMovies(),
      getTopRatedMovies(),
      getUpcomingMovies(),
    ])
      .then(([trend, top, up]) => {
        if (cancelled) return;
        setTrending(trend || []);
        setTopRated(top || []);
        setUpcoming(filterFutureMovies(up || []));
      })
      .catch((err) => {
        console.error(err);
        if (cancelled) return;
        setTrending([]);
        setTopRated([]);
        setUpcoming([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#08070C] text-white">
      <Navbar />

      <DashboardHero movies={trending} />

      <section className="dc-how-section" id="how-it-works">
        <div className="dc-how-intro">
          <span className="dc-slider-eyebrow">A LITTLE MORE YOU</span>
          <h2>Not another endless<br /><em>scrolling session.</em></h2>
          <p>{userId ? "Your viewing activity helps shape a more relevant mix of films over time." : "Start with a few films you love. DeepCine brings discovery, your watchlist and recommendations into one place."}</p>
        </div>
        <div className="dc-how-grid">
          {HOW_IT_WORKS.map(({ icon: Icon, title, description }, index) => (
            <article key={title} className="dc-how-card">
              <span className="dc-how-index">0{index + 1}</span>
              <Icon size={19} />
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <MoodBrowser />

      <PersonalizedMovies />

      <CollaborativeMovies />

      <div id="trending">
        <MovieSlider
          title="🔥 Trending Movies"
          movies={trending}
          loading={loading}
          seeMoreState={{ mode: "trending", title: "Trending Movies" }}
        />
      </div>

      <div id="top-rated">
        <MovieSlider
          title="⭐ Top Rated Movies"
          movies={topRated}
          loading={loading}
          seeMoreState={{ mode: "top-rated", title: "Top Rated Movies" }}
        />
      </div>

      <div id="upcoming">
        <MovieSlider
          title="📅 Upcoming Movies"
          movies={upcoming}
          loading={loading}
          seeMoreState={{ mode: "upcoming", title: "Upcoming Movies" }}
        />
      </div>
    </div>
  );
}
