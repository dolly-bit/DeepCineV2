import { useEffect, useState } from "react";
import { getPersonalizedRecommendations } from "../services/movies";
import RecommendationSection from "./RecommendationSection";
import { getAuthState } from "../services/auth";

export default function PersonalizedMovies() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRecommendations = async () => {
      const { userId } = getAuthState();

      if (!userId) {
        setMovies([]);
        setLoading(false);
        return;
      }

      try {
        const data = await getPersonalizedRecommendations(userId);
        setMovies(data || []);
      } catch (error) {
        console.error(
          "Failed to load personalized recommendations:",
          error
        );
        setMovies([]);
      } finally {
        setLoading(false);
      }
    };

    loadRecommendations();
  }, []);

  const { userId } = getAuthState();
  if (!userId) return null;

  return (
    <RecommendationSection
      movies={movies}
      loading={loading}
      eyebrow="Personalized · powered by your watch history"
      title="✨ Recommended For You"
      description="Blends semantic movie similarity, your watch and rating signals, genre preferences, and collaborative patterns when enough cross-user data is available."
      emptyMessage="Watch a few movies (click into any title's page) and we'll start building your personalized recommendations here."
      seeMoreState={{ mode: "recommended", title: "Recommended For You" }}
    />
  );
}