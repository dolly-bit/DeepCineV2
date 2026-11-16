import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Mail, User as UserIcon, ShieldCheck, X, Clapperboard } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import HomeSidebar from "../components/layout/HomeSidebar";
import { getAuthState, getCurrentUser, clearAuthState } from "../services/auth";

export default function Profile() {
  const navigate = useNavigate();
  const { username: cachedUsername } = getAuthState();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getCurrentUser();
        if (!cancelled) setUser(data);
      } catch (err) {
        if (!cancelled) setError("We couldn't load your account details. Please try again.");
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const handleLogout = () => {
    clearAuthState();
    navigate("/", { replace: true });
  };

  const displayName = user?.username || cachedUsername || "Your Account";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div className="dc-app-shell">
      <HomeSidebar />
      <main className="dc-app-main dc-profile-page">
        <Navbar />
        <section className="dc-profile-content">
          <div className="dc-profile-heading">
            <div>
              <span className="dc-profile-eyebrow">YOUR SPACE</span>
              <h1>Account profile</h1>
              <p>Manage your DeepCine identity and session.</p>
            </div>
            <button type="button" onClick={() => navigate("/home")} className="dc-profile-close" aria-label="Back to home">
              <X size={17} />
            </button>
          </div>

          <article className="dc-profile-card">
            <div className="dc-profile-card-top">
              <div className="dc-profile-avatar">{initial}</div>
              <div className="dc-profile-identity">
                <span className="dc-profile-kicker"><Clapperboard size={13} /> DEEPCINE MEMBER</span>
                <h2>{displayName}</h2>
                <p>Your personal cinema account</p>
              </div>
              <span className="dc-profile-status"><span /> Active</span>
            </div>

            {loading ? (
              <div className="dc-profile-loading">
                <span /><span /><span />
              </div>
            ) : error ? (
              <div className="dc-profile-error">{error}</div>
            ) : (
              <div className="dc-profile-details">
                <div className="dc-profile-detail">
                  <span className="dc-profile-detail-icon"><UserIcon size={18} /></span>
                  <div><small>USERNAME</small><strong>{user?.username || displayName}</strong></div>
                </div>
                <div className="dc-profile-detail">
                  <span className="dc-profile-detail-icon"><Mail size={18} /></span>
                  <div><small>EMAIL ADDRESS</small><strong>{user?.email || "Not available"}</strong></div>
                </div>
                <div className="dc-profile-detail">
                  <span className="dc-profile-detail-icon"><ShieldCheck size={18} /></span>
                  <div><small>ACCOUNT SECURITY</small><strong>Signed in · Session active</strong></div>
                </div>
              </div>
            )}

            <div className="dc-profile-card-footer">
              <p>Enjoy your next movie.</p>
              <button type="button" onClick={handleLogout} className="dc-profile-logout">
                <LogOut size={16} /> Sign out
              </button>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
