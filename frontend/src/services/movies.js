import api from "./api";

const normalizeMovie = (movie) => ({
  id: movie.id ?? movie.tmdb_id,
  title: movie.title || "Untitled movie",
  overview: movie.overview || "A great pick for your next watch.",
  poster_url: movie.poster_url || (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null),
  poster_path: movie.poster_path,
  release_date: movie.release_date || null,
  vote_average: movie.vote_average ?? 0,
  ...movie,
});

const safeRequest = async (request) => {
  try {
    const res = await request();
    return Array.isArray(res?.data) ? res.data.map(normalizeMovie) : [];
  } catch (err) {
    console.error(err);
    return [];
  }
};

// Trending Movies
export const getTrendingMovies = async () =>
  safeRequest(() => api.get("/movies/trending"));

// Top Rated Movies
export const getTopRatedMovies = async () =>
  safeRequest(() => api.get("/movies/top-rated"));

// Upcoming Movies
export const getUpcomingMovies = async () =>
  safeRequest(() => api.get("/movies/upcoming"));

// Search Movies
export const searchMovies = async (query) =>
  safeRequest(() => api.get("/movies/search", { params: { query } }));

// AI Recommendations
export const getRecommendations = async (movieName) =>
  safeRequest(() =>
    api.get("/recommend/content", { params: { movie_name: movieName } })
  );

// Content-Based Recommendations
export const getContentRecommendations = async (movieName) =>
  safeRequest(() =>
    api.get("/recommend/content", { params: { movie_name: movieName } })
  );

// Collaborative Filtering
export const getCollaborativeRecommendations = async (userId) => {
  if (!userId) return [];

  try {
    const res = await api.get(
      `/recommend/collaborative/${userId}`
    );

    return (res.data || []).map(normalizeMovie);
  } catch (err) {
    console.error("Collaborative recommendation error:", err);
    return [];
  }
};

export const getMovieDetails = async (id) => {
  const res = await api.get(`/movies/${id}`);
  return res.data;
};

export const getMovieTrailer = async (id) => {
  const response = await api.get(`/movies/${id}/trailer`);
  return response.data;
};

export const getMovieCast = async (id) => {
  const response = await api.get(`/movies/${id}/cast`);
  return response.data;
};

export const getSimilarMovies = async (id) => {
  const response = await api.get(`/movies/${id}/similar`);
  return response.data;
};


export const saveWatchHistory = async (userId, tmdbId) => {
  const res = await api.post("/watch-history", null, {
    params: {
      user_id: userId,
      tmdb_id: tmdbId,
    },
  });

  return res.data;
};

export const saveSearchHistory = async (userId, query) => {
  const res = await api.post("/search-history/", null, {
    params: {
      user_id: userId,
      query: query,
    },
  });

  return res.data;
};

// Fire-and-forget helper: records a search against the logged-in user's
// history (used to power the "Because you searched..." row and, over
// time, better personalization) without ever blocking or breaking the
// search UI if it fails or the user isn't logged in.
export const recordSearch = (query) => {
  if (!query || !query.trim()) return;

  const userId = localStorage.getItem("user_id");
  if (!userId || userId === "undefined") return;

  saveSearchHistory(userId, query.trim()).catch(() => {
    // Non-critical: never surface this to the user.
  });
};

// Fire-and-forget helper: records that a user opened a movie's details
// (i.e. clicked "More Info" / a poster) into their watch history, which
// is the core signal the collaborative-filtering model trains on.
export const recordWatch = (tmdbId) => {
  if (!tmdbId) return;

  const userId = localStorage.getItem("user_id");
  if (!userId || userId === "undefined") return;

  saveWatchHistory(userId, tmdbId).catch(() => {
    // Non-critical: never surface this to the user.
  });
};

// Personalized AI Recommendations
export const getPersonalizedRecommendations = async (userId) => {
  if (!userId) return [];

  const res = await api.get(
    `/recommend/personalized/${userId}`
  );

  return (res.data || []).map(normalizeMovie);
};

// Discover: browse by mood / genre / language
export const getMoods = async () => {
  const res = await api.get("/movies/moods");
  return res.data || [];
};

export const getGenres = async () => {
  const res = await api.get("/movies/genres");
  return res.data || [];
};

export const getLanguages = async () => {
  const res = await api.get("/movies/languages");
  return res.data || [];
};

export const discoverMovies = async ({ mood, genres, language, sortBy, page = 1 } = {}) =>
  safeRequest(() =>
    api.get("/movies/discover", {
      params: {
        mood: mood || undefined,
        genres: genres && genres.length ? genres.join(",") : undefined,
        language: language || undefined,
        sort_by: sortBy || undefined,
        page,
      },
    })
  );