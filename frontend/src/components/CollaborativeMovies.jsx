import { useEffect, useState } from "react";
import { getCollaborativeRecommendations } from "../services/movies";
import RecommendationSection from "./RecommendationSection";
import { getAuthState } from "../services/auth";

/**
 * Surfaces genuine collaborative-filtering output (ALS matrix
 * factorization trained on cross-user watch history — see
 * backend/ai/collaborative.py) directly on the home page, so the
 * "personalized, collaborative-filtering-powered" nature of the app is
 * visible, not just something happening invisibly on the backend.
 *
 * Renders nothing until the CF model has learned enough about this user
 * (which requires a trained cf_model.pkl and this user having watch
 * history in it) — that's expected/normal for a fresh account.
 */
export default function CollaborativeMovies() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const { userId } = getAuthState();

      if (!userId) {
        setMovies([]);
        setLoading(false);
        return;
      }

      try {
        const data = await getCollaborativeRecommendations(userId);
        setMovies(data || []);
      } catch (error) {
        console.error("Failed to load collaborative recommendations:", error);
        setMovies([]);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (!loading && movies.length === 0) return null;

  return (
    <RecommendationSection
      movies={movies}
      loading={loading}
      eyebrow="Collaborative filtering"
      title="🤝 Viewers Like You Also Watched"
      description="Matched with people who share your watch patterns — not your genres, your actual taste."
    />
  );
}
