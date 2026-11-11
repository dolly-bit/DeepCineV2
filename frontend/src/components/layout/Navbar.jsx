import { Film, Search, Menu, X, UserRound, LogOut, Compass, Sparkles } from "lucide-react";
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

  const go = (path) => { setMenuOpen(false); navigate(path); };
  const signOut = () => { clearAuthState(); setMenuOpen(false); navigate("/", { replace: true }); };
  const navItems = authenticated
    ? [{ label: "For you", path: "/home" }, { label: "Discover", path: "/discover" }, { label: "AI picks", path: "/recommend" }, { label: "My list", path: "/profile" }]
    : [{ label: "Discover", path: "/#trending" }, { label: "How it works", path: "/#how-it-works" }];

  return (
    <header className="dc-nav">
      <div className="dc-nav-inner">
        <Link to={authenticated ? "/home" : "/"} className="dc-brand">
          <span className="dc-brand-mark"><Film size={18} /></span>
          <span>DEEP<span>CINE</span></span>
        </Link>

        <nav className="dc-nav-links" aria-label="Main navigation">
          {navItems.map((item) => <Link key={item.label} className={location.pathname === item.path ? "active" : ""} to={item.path}>{item.label}</Link>)}
          <button type="button" onClick={() => setSearchOpen(true)} className="inline-flex items-center gap-2"><Search size={14} /> Search</button>
        </nav>

        <div className="dc-nav-actions">
          {authenticated ? (
            <>
              <button type="button" className="dc-nav-ghost" onClick={() => go("/profile")}><UserRound size={14} /> {username || "Account"}</button>
              <button type="button" className="dc-nav-cta" onClick={signOut}>Sign out <LogOut size={14} /></button>
            </>
          ) : (
            <>
              <Link to="/login" className="dc-nav-ghost">Sign in</Link>
              <Link to="/signup" className="dc-nav-cta">Get started <Sparkles size={14} /></Link>
            </>
          )}
        </div>

        <button type="button" className="dc-mobile-toggle" aria-label={menuOpen ? "Close menu" : "Open menu"} aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}>{menuOpen ? <X size={22} /> : <Menu size={22} />}</button>
      </div>

      {menuOpen && <nav className="dc-mobile-menu" aria-label="Mobile navigation">
        {navItems.map((item) => <Link key={item.label} to={item.path} onClick={() => setMenuOpen(false)}>{item.label}</Link>)}
        <button type="button" onClick={() => { setMenuOpen(false); setSearchOpen(true); }}>Search movies</button>
        {authenticated ? <><Link to="/profile" onClick={() => setMenuOpen(false)}>My profile</Link><button type="button" onClick={signOut}>Sign out</button></> : <><Link to="/login" onClick={() => setMenuOpen(false)}>Sign in</Link><Link to="/signup" onClick={() => setMenuOpen(false)}>Create account</Link></>}
      </nav>}
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </header>
  );
}
