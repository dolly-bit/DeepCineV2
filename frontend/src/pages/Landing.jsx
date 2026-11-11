import { useEffect, useState } from "react";

import Navbar from "../components/layout/Navbar";
import Hero from "../components/home/Hero";
import TrendingMarquee from "../components/home/TrendingMarquee";

import { getTrendingMovies } from "../services/movies";

export default function Landing() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadMovies() {
    try {
      const data = await getTrendingMovies();
      setMovies(data);
    } catch (err) {
      console.error(err);
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

      <Navbar publicMode hideSearch />

      <Hero movies={movies} loading={loading} />

      <TrendingMarquee
        movies={movies}
        loading={loading}
      />

    </div>
  );
}
