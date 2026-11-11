import { Compass, Home, Library, Sparkles, Star, Clock3, Search } from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
const items = [
  { label: "Home", to: "/home", icon: Home, end: true },
  { label: "Explore", to: "/discover", icon: Compass },
  { label: "AI Picks", to: "/recommend", icon: Sparkles },
  { label: "My Library", to: "/library", icon: Library },
  { label: "Recently Added", to: "/movies", icon: Clock3, state: { mode: "recent", title: "Recently Added" } },
  { label: "Top Rated", to: "/movies", icon: Star, state: { mode: "top-rated", title: "Top Rated" } },
];
export default function HomeSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  return <aside className="dc-side-panel">
    <NavLink to="/home" className="dc-side-brand"><span className="dc-side-mark">D</span><span>Deep<span>Cine</span></span></NavLink>
    <div className="dc-side-label">LIBRARY</div>
    <nav className="dc-side-nav" aria-label="Library navigation">
      {items.map(({ label, to, icon: Icon, end, state }) => <NavLink
        key={label}
        to={state ? { pathname: to, state } : to}
        end={end}
        className={({ isActive }) => {
          const modeMatches = !state || (label === "Recently Added"
            ? location.state?.mode === "recent"
            : location.state?.mode === "top-rated");
          return "dc-side-link" + (isActive && modeMatches ? " active" : "");
        }}
      ><Icon size={17}/><span>{label}</span></NavLink>)}
    </nav>
    <div className="dc-side-spacer"/>
    <button className="dc-side-search" onClick={() => navigate("/discover")}><Search size={16}/> Search catalogue</button>
    <div className="dc-side-footer"><span className="dc-side-status"/> YOUR PERSONAL CINEMA</div>
  </aside>;
}