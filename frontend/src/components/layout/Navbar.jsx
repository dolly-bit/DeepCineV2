import { Search, Bell, UserRound, LogOut, Menu, X, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import SearchModal from "../SearchModal";
import { clearAuthState, getAuthState } from "../../services/auth";
export default function Navbar({ publicMode = false, hideSearch = false } = {}) {
  const navigate=useNavigate(); const [searchOpen,setSearchOpen]=useState(false); const [menuOpen,setMenuOpen]=useState(false);
  const {accessToken,userId,username}=getAuthState(); const authenticated=Boolean(accessToken&&userId&&userId!=="undefined");
  const signOut=()=>{clearAuthState();navigate("/",{replace:true});};
  return <header className={`dc-dashboard-topbar${publicMode ? " dc-landing-topbar" : ""}`}>
    {!hideSearch && <div className="dc-topbar-search"><Search size={17}/><button onClick={()=>setSearchOpen(true)}>Search for films, directors, or actors...</button><kbd>⌘ K</kbd></div>}
    <div className="dc-topbar-actions">
      <button className="dc-topbar-icon" aria-label="Notifications"><Bell size={17}/></button>
      {authenticated && !publicMode ? <><button className="dc-topbar-user" onClick={()=>navigate("/profile")}><span className="dc-user-avatar"><UserRound size={16}/></span><span><strong>{username||"Your account"}</strong><small>Personal cinema</small></span></button><button className="dc-topbar-icon" aria-label="Sign out" onClick={signOut}><LogOut size={16}/></button></>:
      <div className="dc-topbar-auth"><Link to="/login">Sign in</Link><Link to="/signup"><Sparkles size={13}/> Join</Link></div>}
      <button className="dc-topbar-mobile" onClick={()=>setMenuOpen(v=>!v)} aria-label="Toggle navigation">{menuOpen?<X size={20}/>:<Menu size={20}/>}</button>
    </div>
    {menuOpen&&<nav className="dc-topbar-mobile-menu"><Link to="/home">Home</Link><Link to="/discover">Explore</Link><Link to="/recommend">AI Picks</Link><Link to="/profile">My Collection</Link></nav>}
    {!hideSearch && <SearchModal isOpen={searchOpen} onClose={()=>setSearchOpen(false)}/ >}
  </header>;
}