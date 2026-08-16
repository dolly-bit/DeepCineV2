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

export default function Home() {
  const [trending, setTrending] = useState([]);
  const [topRated, setTopRated] = useState([]);
  const [upcoming, setUpcoming] = useState([]);

  const [loading, setLoading] = useState(true);

  const { userId } = getAuthState();

  const filterFutureMovies = (movies) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return movies
      .filter((movie) => {
        if (!movie.release_date) return false;
        const releaseDate = new Date(movie.release_date);
        return !Number.isNaN(releaseDate.getTime()) && releaseDate >= today;
      })
      .sort((a, b) => new Date(a.release_date) - new Date(b.release_date));
  };

  async function loadMovies() {
    try {
      const [trend, top, up] = await Promise.all([
        getTrendingMovies(),
        getTopRatedMovies(),
        getUpcomingMovies(),
      ]);

      setTrending(trend || []);
      setTopRated(top || []);
      setUpcoming(filterFutureMovies(up || []));
    } catch (err) {
      console.error(err);
      setTrending([]);
      setTopRated([]);
      setUpcoming([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMovies();
  }, []);

  return (
    <div className="min-h-screen bg-[#08070C] text-white">
      <Navbar />

      <DashboardHero movies={trending} />

      {/* System branding: makes it unmistakably clear this is a
          personalized, collaborative-filtering-powered recommender,
          not just a generic movie browser. */}
      <section className="max-w-7xl mx-auto px-6 mt-10">
        <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-purple-600/15 via-white/5 to-cyan-500/10 p-5 sm:p-6">
          <p className="text-[11px] uppercase tracking-[0.3em] text-purple-300">
            DeepCine
          </p>
          <h2 className="mt-1.5 text-xl sm:text-2xl font-semibold text-white">
            A personalized movie recommendation system
          </h2>
          <p className="mt-1.5 max-w-3xl text-xs text-slate-300">
            {userId
              ? "Your picks below are being generated live from your watch history and search activity."
              : "Sign up and start watching to unlock recommendations built just for you."}
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {HOW_IT_WORKS.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-xl border border-white/10 bg-black/20 p-3"
              >
                <Icon size={15} className="text-purple-300" />
                <p className="mt-2 text-xs font-semibold text-white">
                  {title}
                </p>
                <p className="mt-1 text-[11px] leading-relaxed text-slate-400">
                  {description}
                </p>
              </div>
            ))}
          </div>
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