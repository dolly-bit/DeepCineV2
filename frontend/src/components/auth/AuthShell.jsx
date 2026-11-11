import { Film, Sparkles, Clapperboard, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

const visualPosters = [
  "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
  "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
  "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
  "https://image.tmdb.org/t/p/w500/8UlWHLMpgZm9bx6QYh0NFoq67TZ.jpg",
];

export default function AuthShell({ eyebrow, title, description, children, footer, mode = "login" }) {
  return (
    <main className="auth-page">
      <div className="auth-grain" aria-hidden="true" />
      <header className="auth-topbar">
        <Link to="/" className="brand-lockup">
          <span className="brand-mark"><Film size={19} strokeWidth={2.2} /></span>
          <span>DEEP<span>CINE</span></span>
        </Link>
        <Link to="/" className="auth-back-link">Back to discovery <ArrowUpRight size={15} /></Link>
      </header>

      <div className="auth-layout">
        <section className="auth-story">
          <div className="auth-kicker"><Sparkles size={14} /> YOUR NEXT SCENE STARTS HERE</div>
          <p className="auth-overline">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="auth-description">{description}</p>

          <div className="poster-orbit" aria-label="A selection of movie posters">
            {visualPosters.map((src, index) => (
              <div className={`orbit-poster orbit-poster-${index + 1}`} key={src}>
                <img src={src} alt="" />
              </div>
            ))}
            <div className="orbit-center"><Clapperboard size={25} /><span>CURATED<br />FOR YOUR TASTE</span></div>
          </div>

          <div className="auth-story-foot">
            <span className="auth-live-dot" /> A more personal way to find what to watch.
          </div>
        </section>

        <section className="auth-form-panel">
          <div className="auth-form-heading">
            <span className="auth-step">{mode === "login" ? "01 / WELCOME BACK" : "01 / JOIN THE CLUB"}</span>
            <h2>{mode === "login" ? "Your seat is waiting." : "Make room for good stories."}</h2>
            <p>{mode === "login" ? "Sign in to pick up where your watchlist left off." : "Create your account and start building a watchlist that feels like you."}</p>
          </div>
          {children}
          <div className="auth-form-footer">{footer}</div>
          <p className="auth-legal">By continuing, you agree to use DeepCine responsibly. Your account stays yours.</p>
        </section>
      </div>
      <footer className="auth-bottom"><span>DEEPCINE © {new Date().getFullYear()}</span><span>BUILT FOR THE LOVE OF FILM</span></footer>
    </main>
  );
}
