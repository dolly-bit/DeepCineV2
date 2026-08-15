import "./index.css";

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home";
import RecommendPage from "./pages/RecommendPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Landing from "./pages/Landing"
import MovieDetails from "./pages/MovieDetails";
import SearchPage  from "./pages/Search";
import MoviesListPage from "./pages/MoviesListPage";
import Profile from "./pages/Profile";
import { isAuthenticated } from "./services/auth";

function ProtectedRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
  <Routes>

    {/* Landing Page */}
    <Route path="/" element={<Landing />} />

    {/* Login */}
    <Route path="/login" element={<Login />} />

    {/* Signup */}
    <Route path="/signup" element={<Signup />} />

    {/* Main Dashboard */}
    <Route
      path="/home"
      element={
        <ProtectedRoute>
          <Home />
        </ProtectedRoute>
      }
    />

    {/* AI Recommendation */}
    <Route
      path="/recommend"
      element={
        <ProtectedRoute>
          <RecommendPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/movie/:id"
      element={
        <ProtectedRoute>
          <MovieDetails />
        </ProtectedRoute>
      }
    />
    <Route
      path="/search"
      element={
        <ProtectedRoute>
          <SearchPage />
        </ProtectedRoute>
      }
    />

    <Route
      path="/movies"
      element={
        <ProtectedRoute>
          <MoviesListPage />
        </ProtectedRoute>
      }
    />

    <Route
      path="/profile"
      element={
        <ProtectedRoute>
          <Profile />
        </ProtectedRoute>
      }
    />


  </Routes>
</BrowserRouter>
  );
}