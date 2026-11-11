import { Film, Search, Menu, X, UserRound, LogOut, Sparkles } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import SearchModal from "../SearchModal";
import { clearAuthState, getAuthState } from "../../services/auth";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { accessToken, userId, username } = getAuthState();
  const authenticated = Boolean(accessToken && userId && userId !== "undefined");
  const signOut = () => { clearAuthState(); setMenuOpen(false); navigate("/", { replace: true }); };
  const navItems = [
    { label: "Home", path: "/home" },
    { label: "Discover", path: "/discover" },
    { label: "Movies", path: "/movies" },
    { label: "AI Picks", path: "/recommend" },
    { label: "My List", path: "/profile" },
  ];

  return (
    <header className="dc-stream-nav">
      <div className="dc-stream-nav-inner">
        <Link to="/home" className="dc-stream-brand" aria-label="DeepCine home">
          <span>DEEP<span>CINE</span></span>
        </Link>
        <nav className="dc-stream-links" aria-label="Main navigation">
          {navItems.filter((item) => authenticated || item.path === "/discover").map((item) => (
            <Link key={item.path} to={item.path} className={location.pathname === item.path ? "active" : ""}>{item.label}</Link>
          ))}
        </nav>
        <div className="dc-stream-actions">
          <button type="button" className="dc-stream-search" onClick={() => setSearchOpen(true)} aria-label="Search movies"><Search size={19} /></button>
          {authenticated ? (
            <>
              <button type="button" className="dc-stream-account" onClick={() => navigate("/profile")}><UserRound size={16} /><span>{username || "Account"}</span></button>
              <button type="button" className="dc-stream-signout" onClick={signOut} aria-label="Sign out"><LogOut size={17} /></button>
            </>
          ) : (
            <><Link to="/login" className="dc-stream-signin">Sign in</Link><Link to="/signup" className="dc-stream-join"><Sparkles size={14} /> Join</Link></>
          )}
        </div>
        <button type="button" className="dc-stream-mobile-toggle" aria-label={menuOpen ? "Close menu" : "Open menu"} aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}>{menuOpen ? <X size={22} /> : <Menu size={22} />}</button>
      </div>
      {menuOpen && <nav className="dc-stream-mobile-menu" aria-label="Mobile navigation">
        {navItems.filter((item) => authenticated || item.path === "/discover").map((item) => <Link key={item.path} to={item.path} onClick={() => setMenuOpen(false)}>{item.label}</Link>)}
        <button type="button" onClick={() => { setMenuOpen(false); setSearchOpen(true); }}>Search movies</button>
        {authenticated ? <button type="button" onClick={signOut}>Sign out</button> : <><Link to="/login" onClick={() => setMenuOpen(false)}>Sign in</Link><Link to="/signup" onClick={() => setMenuOpen(false)}>Create account</Link></>}
      </nav>}
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </header>
  );
}
