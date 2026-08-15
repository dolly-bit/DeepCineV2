import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Search } from "lucide-react";

import Navbar from "../components/layout/Navbar";
import DashboardHero from "../components/home/DashboardHero";
import RecommendationSection from "../components/RecommendationSection";
import { getAuthState } from "../services/auth";

import {
  getTrendingMovies,
  getTopRatedMovies,
  getUpcomingMovies,
  getRecommendations,
  getCollaborativeRecommendations,
  getPersonalizedRecommendations,
  recordSearch,
} from "../services/movies";

export default function RecommendPage() {
  const location = useLocation();
  const { userId, username } = getAuthState();

  // Only show "Because you searched" if the user actually arrived here
  // via a search (from Search.jsx / SearchModal / Hero / FilterBar) -
  // previously this defaulted to a hardcoded "Avengers" search on every
  // direct visit, which made no sense.
  const initialSearch = location.state?.search || "";

  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [activeSearch, setActiveSearch] = useState(initialSearch);

  const [recommended, setRecommended] = useState([]);
  const [personalized, setPersonalized] = useState([]);
  const [collaborative, setCollaborative] = useState([]);
  const [trending, setTrending] = useState([]);
  const [topRated, setTopRated] = useState([]);
  const [upcoming, setUpcoming] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const filterFutureMovies = (movies) => {
    const today = new Date().toISOString().slice(0, 10);
    return movies
      .filter((movie) => movie.release_date && movie.release_date >= today)
      .sort((a, b) => a.release_date.localeCompare(b.release_date));
  };

  const loadMovies = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        recommend,
        personalizedMovies,
        collaborativeMovies,
        trendingMovies,
        topRatedMovies,
        upcomingMovies,
      ] = await Promise.all([
        activeSearch ? getRecommendations(activeSearch) : Promise.resolve([]),
        getPersonalizedRecommendations(userId),
        getCollaborativeRecommendations(userId),
        getTrendingMovies(),
        getTopRatedMovies(),
        getUpcomingMovies(),
      ]);

      setRecommended(recommend || []);
      setPersonalized(personalizedMovies || []);
      setCollaborative(collaborativeMovies || []);
      setTrending(trendingMovies || []);
      setTopRated(topRatedMovies || []);
      setUpcoming(filterFutureMovies(upcomingMovies || []));
    } catch (err) {
      console.error(err);
      setError("Failed to load movies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMovies();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSearch, userId]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    recordSearch(searchTerm);
    setActiveSearch(searchTerm.trim());
  };

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cm-bg text-red-400">
        {error}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cm-bg font-sans">
      <Navbar />

      <DashboardHero movies={trending} />

      <section className="mx-auto -mt-10 max-w-2xl px-6">
        <form
          onSubmit={handleSearch}
          className="flex items-center gap-2 rounded-xl border border-cm-line bg-cm-surface p-1.5 text-sm shadow-[0_14px_40px_rgba(8,7,12,0.6)] backdrop-blur"
        >
          <Search size={15} className="ml-2 text-cm-muted" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={
              username
                ? `Hi ${username} — search a movie to sharpen your recommendations...`
                : "Search a movie to sharpen your recommendations..."
            }
            className="flex-1 bg-transparent text-white outline-none placeholder:text-cm-muted"
          />
          <button
            type="submit"
            className="rounded-lg bg-gradient-to-r from-cm-purple-deep to-cm-purple px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
          >
            Search
          </button>
        </form>
      </section>

      <RecommendationSection
        movies={personalized}
        loading={loading}
        eyebrow="Personalized"
        title="Recommended For You"
        description="A mix of your watch history and genre affinity."
        emptyMessage={
          userId
            ? "Watch a few movies and we'll start building this for you."
            : "Log in to see recommendations personalized to you."
        }
      />

      {activeSearch && (
        <RecommendationSection
          movies={recommended}
          loading={loading}
          eyebrow="Content-based"
          title={`Because You Searched "${activeSearch}"`}
          description="Movies with similar themes, tone, and story."
          emptyMessage={`No close matches found for "${activeSearch}".`}
        />
      )}

      <RecommendationSection
        movies={collaborative}
        loading={loading}
        eyebrow="Collaborative filtering"
        title="Viewers Like You Also Watched"
        description="Matched with people who share your watch patterns."
        emptyMessage={
          userId
            ? null // stays hidden entirely when empty & logged in - not enough data yet
            : "Log in to unlock collaborative recommendations."
        }
      />

      <RecommendationSection
        movies={trending}
        loading={loading}
        eyebrow="This week"
        title="Trending Movies"
        description="What everyone's watching right now."
      />

      <RecommendationSection
        movies={upcoming}
        loading={loading}
        eyebrow="Coming soon"
        title="Upcoming Movies"
        description="Mark your calendar."
      />

      <RecommendationSection
        movies={topRated}
        loading={loading}
        eyebrow="All-time"
        title="Top Rated Movies"
        description="Highest rated by audiences."
      />

      <footer className="px-6 py-10 text-center text-xs text-cm-muted">
        © 2026 DeepCine
      </footer>
    </div>
  );
}
