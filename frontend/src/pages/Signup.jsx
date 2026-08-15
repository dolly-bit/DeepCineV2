import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Film, Sparkles, Play, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import api from "../services/api";

export default function Signup() {
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [formKey, setFormKey] = useState(0);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const resetForm = () => {
    setForm({ username: "", email: "", password: "" });
  };

  useEffect(() => {
    // Reset the form whenever the user navigates back to this route
    // (e.g. Login <-> Signup). This is the standard "reset on route
    // change" pattern; disabling the stricter set-state-in-effect lint
    // rule here is intentional, not an oversight.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    resetForm();
    setShowPassword(false);
    setError("");
    setFormKey((prev) => prev + 1);
  }, [location.pathname, location.key]);

  const handleSignup = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");

    try {
      await api.post("/auth/register", form);
      resetForm();
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }

    setLoading(false);
  };

  const posterUrl = "https://image.tmdb.org/t/p/w500/8UlWHLMpgZm9bx6QYh0NFoq67TZ.jpg";

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#03050a] px-4 py-10 text-white sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(168,85,247,0.28),_transparent_32%),radial-gradient(circle_at_bottom_right,_rgba(34,211,238,0.22),_transparent_36%)]" />
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#03050a]/90 via-[#03050a]/70 to-[#03050a]/95" />
      </div>
      <motion.div
        animate={{ y: [0, -18, 0], x: [0, 16, 0], rotate: [0, 8, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute left-[-8%] top-10 h-64 w-64 rounded-full bg-fuchsia-600/20 blur-3xl"
      />
      <motion.div
        animate={{ y: [0, 22, 0], x: [0, -16, 0], rotate: [0, -6, 0] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[-5%] right-[-4%] h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl"
      />
      <motion.div
        animate={{ scale: [1, 1.04, 1], opacity: [0.8, 1, 0.8] }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
        className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-purple-700/20 to-transparent"
      />

      <div className="relative z-10 mx-auto flex min-h-[85vh] max-w-6xl flex-col items-center justify-center rounded-[32px] border border-white/10 bg-black/50 p-6 shadow-[0_30px_120px_rgba(0,0,0,0.45)] backdrop-blur-xl lg:flex-row lg:gap-10 lg:p-10">
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden rounded-[32px]">
          <img src={posterUrl} alt="movie poster" className="h-full w-full object-cover object-center opacity-40" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#03050a]/90 via-[#03050a]/65 to-[#03050a]/85" />
        </div>
        <div className="mb-8 max-w-xl text-center lg:mb-0 lg:text-left">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-purple-500/40 bg-purple-500/10 px-4 py-2 text-sm font-medium text-purple-200">
            <Film size={16} />
            DeepCine : Your Personal Movie Assistant
          </div>

          <h1 className="text-4xl font-black leading-tight sm:text-5xl">
            Your cinematic identity starts here.
          </h1>

          <p className="mt-4 text-lg leading-8 text-slate-300">
            Join the experience and get personalized recommendations, fresh trending picks, and a watchlist shaped by your taste.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
              <Sparkles size={16} className="text-fuchsia-400" />
              Personalized picks
            </div>
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
              <Play size={16} className="text-cyan-400" />
              Smart discovery
            </div>
          </div>
        </div>

        <div className="w-full max-w-md rounded-[28px] border border-white/10 bg-[#090b14]/90 p-7 shadow-2xl shadow-purple-950/20">
          <h2 className="text-3xl font-bold text-white">Create Account</h2>
          <p className="mt-2 text-sm text-slate-400">Join DeepCine and unlock your watchlist</p>

          {error && (
            <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <form key={formKey} onSubmit={handleSignup} className="mt-6 space-y-4">
            <input
              type="text"
              name="username"
              placeholder="Username"
               autoComplete="off"
              value={form.username}
              onChange={handleChange}
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition focus:border-purple-500 focus:bg-white/10"
            />

            <input
              type="email"
              name="email"
               autoComplete="off"
              placeholder="Email"
              value={form.email}
              onChange={handleChange}
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition focus:border-purple-500 focus:bg-white/10"
            />

            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Password"
                autoComplete="new-password"
                value={form.password}
                onChange={handleChange}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 pr-12 text-white outline-none transition focus:border-purple-500 focus:bg-white/10"
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-fuchsia-500 px-4 py-3 font-semibold text-white transition hover:scale-[1.01] hover:shadow-lg hover:shadow-fuchsia-500/20"
            >
              {loading ? "Creating Account..." : <>Create Account <ArrowRight size={18} /></>}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{" "}
            <Link to="/login" onClick={resetForm} className="ml-2 font-medium text-purple-300 hover:text-purple-200">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}