import { Sparkles, Search, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import SearchModal from "../SearchModal";
import {getAuthState, clearAuthState,} from "../../services/auth"

export default function Navbar() {
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);

  const { accessToken, userId, username } = getAuthState();
  const isAuthenticated = Boolean(accessToken) && Boolean(userId) && userId !== "undefined";

  const logout = () => {
    clearAuthState();
    navigate("/");
  };

  return (
    <nav className="sticky top-0 z-50 bg-[#08070C]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto flex items-center justify-between h-16 px-6 lg:px-10">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <Sparkles className="text-purple-400" size={18} />
          <h1 className="text-xl font-bold tracking-wider text-white">
            DeepCine
          </h1>
        </Link>

        {/* Menu */}
        <div className="hidden md:flex items-center gap-8 text-gray-300">

          <button
            type="button"
            onClick={() => navigate("/movies", { state: { mode: "trending", title: "Trending Movies" } })}
            className="hover:text-white"
          >
            Trending
          </button>

          <button
            type="button"
            onClick={() => navigate("/movies", { state: { mode: "recommended", title: "Recommended For You", query: "Avengers" } })}
            className="hover:text-white"
          >
            AI Recommend
          </button>

          <button
            onClick={() => setSearchOpen(true)}
            className="hover:text-white flex items-center gap-2 transition"
          >
            <Search size={16} />
            Search
          </button>

        </div>

        {/* Right Side */}
        <div className="flex items-center gap-3">

         
           {!isAuthenticated ? (
            <>
              <button
                onClick={() => navigate("/login")}
                className="px-5 py-2 rounded-full bg-purple-600 hover:bg-purple-700 font-semibold transition"
              >
                Login
              </button>

              <button
                onClick={() => navigate("/signup")}
                className="px-5 py-2 rounded-full border border-purple-500 text-white hover:bg-purple-600 transition"
              >
                Sign Up
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => navigate("/profile")}
                className="hidden sm:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 transition hover:border-cm-purple/50 hover:bg-white/10"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 text-xs font-bold text-white">
                  {(username || "U").charAt(0).toUpperCase()}
                </div>
                <span className="text-sm text-slate-200">
                  {username || "Account"}
                </span>
              </button>

              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-600 hover:bg-red-700 transition"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          )}
         

        </div>

      </div>
      <SearchModal
      isOpen={searchOpen}
      onClose={()=>
        setSearchOpen(false)
      }/>
    </nav>
  );
}