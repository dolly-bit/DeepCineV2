import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Mail, User as UserIcon, ShieldCheck } from "lucide-react";

import Navbar from "../components/layout/Navbar";
import { getAuthState, getCurrentUser, clearAuthState } from "../services/auth";

export default function Profile() {
  const navigate = useNavigate();
  const { username: cachedUsername } = getAuthState();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch (err) {
        // A 401 here is already handled globally (api.js clears the
        // session and redirects to /login), so this only fires for
        // genuine network/server errors.
        setError("Couldn't load your profile right now.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const handleLogout = () => {
    clearAuthState();
    navigate("/");
  };

  const displayName = user?.username || cachedUsername || "Your Account";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div className="min-h-screen bg-cm-bg text-white">
      <Navbar />

      <section className="mx-auto max-w-3xl px-6 py-16">
        <div className="rounded-[32px] border border-cm-line bg-cm-surface p-8 sm:p-10">
          <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cm-purple-deep to-cm-purple text-3xl font-bold text-white">
              {initial}
            </div>

            <div>
              <h1 className="text-3xl font-bold text-white">
                {displayName}
              </h1>
              <p className="mt-1 text-sm text-cm-muted">
                Your DeepCine account
              </p>
            </div>
          </div>

          {loading && (
            <div className="mt-10 space-y-3">
              <div className="h-5 w-2/3 animate-pulse rounded-full bg-white/10" />
              <div className="h-5 w-1/2 animate-pulse rounded-full bg-white/10" />
            </div>
          )}

          {!loading && error && (
            <div className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-300">
              {error}
            </div>
          )}

          {!loading && user && (
            <div className="mt-10 space-y-4">
              <div className="flex items-center gap-3 rounded-2xl border border-cm-line bg-black/20 px-5 py-4">
                <UserIcon size={18} className="text-cm-purple" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-cm-muted">
                    Username
                  </p>
                  <p className="text-sm font-medium text-white">
                    {user.username}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-2xl border border-cm-line bg-black/20 px-5 py-4">
                <Mail size={18} className="text-cm-purple" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-cm-muted">
                    Email
                  </p>
                  <p className="text-sm font-medium text-white">
                    {user.email}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-2xl border border-cm-line bg-black/20 px-5 py-4">
                <ShieldCheck size={18} className="text-emerald-400" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-cm-muted">
                    Session
                  </p>
                  <p className="text-sm font-medium text-white">
                    Signed in and verified
                  </p>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            className="mt-10 flex w-full items-center justify-center gap-2 rounded-2xl bg-red-600 px-6 py-4 font-semibold text-white transition hover:bg-red-700"
          >
            <LogOut size={18} />
            Log Out
          </button>
        </div>
      </section>
    </div>
  );
}
