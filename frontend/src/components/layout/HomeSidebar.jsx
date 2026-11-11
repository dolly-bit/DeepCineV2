import { Compass, Home, Library, Sparkles, Film, Search } from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
const items = [
  { label: "Home", to: "/home", icon: Home, end: true },
  { label: "Movie Collections", to: "/movies", icon: Film, state: { mode: "trending", title: "Movie Collections" } },
  { label: "Explore", to: "/discover", icon: Compass },
  { label: "AI Picks", to: "/recommend", icon: Sparkles },
  { label: "My Library", to: "/library", icon: Library },
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
        className={({ isActive }) => "dc-side-link" + (isActive ? " active" : "")}
      ><Icon size={17}/><span>{label}</span></NavLink>)}
    </nav>
    <div className="dc-side-spacer"/>
    <button className="dc-side-search" onClick={() => navigate("/discover")}><Search size={16}/> Search catalogue</button>
    <div className="dc-side-footer"><span className="dc-side-status"/> YOUR PERSONAL CINEMA</div>
  </aside>;
}