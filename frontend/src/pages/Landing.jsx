import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowDown, ArrowRight, BookmarkPlus, Clapperboard, Compass, Play, Search, Sparkles, Star, Users, WandSparkles } from "lucide-react";
import TrendingMarquee from "../components/home/TrendingMarquee";
import { getTrendingMovies, recordSearch, searchMovies } from "../services/movies";
import "./Landing.css";

const posterOf = (m) => m?.poster_url || (m?.poster_path ? `https://image.tmdb.org/t/p/w500${m.poster_path}` : "");
const backdropOf = (m) => m?.backdrop_url || (m?.backdrop_path ? `https://image.tmdb.org/t/p/original${m.backdrop_path}` : "");

export default function Landing() {
  const [movies,setMovies]=useState([]),[loading,setLoading]=useState(true),[query,setQuery]=useState(""),[searching,setSearching]=useState(false);
  const navigate=useNavigate();
  useEffect(()=>{let active=true;getTrendingMovies().then(data=>{if(active)setMovies(Array.isArray(data)?data:[])}).catch(err=>console.error("Unable to load trending movies:",err)).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[]);
  const featured=useMemo(()=>movies.find(m=>backdropOf(m)&&posterOf(m))||movies.find(m=>posterOf(m))||null,[movies]);
  const backdrop=backdropOf(featured)||"https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg";
  const preview=movies.filter(m=>posterOf(m)).slice(0,6);
  async function handleSearch(e){e.preventDefault();const term=query.trim();if(!term||searching)return;setSearching(true);recordSearch(term);try{const results=await searchMovies(term);navigate("/recommend",{state:{search:term,movies:results}})}catch(err){console.error("Movie search failed:",err);navigate("/recommend",{state:{search:term}})}finally{setSearching(false)}}
  return <main className="dc-cinema-landing">
    <header className="dc-cinema-header">
      <Link to="/" className="dc-cinema-brand"><span className="dc-brand-mark"><Clapperboard size={19}/></span><span>Deep<span>Cine</span></span></Link>
      <nav className="dc-cinema-nav"><a href="#discover">Discover</a><a href="#how-it-works">How it works</a><a href="#trending">Trending</a></nav>
      <div className="dc-cinema-account"><Link to="/login" className="dc-cinema-signin">Sign in</Link><Link to="/signup" className="dc-cinema-join">Get started <ArrowRight size={14}/></Link></div>
    </header>
    <section className="dc-cinema-hero" id="discover">
      <div className="dc-cinema-backdrop" style={{backgroundImage:`url("${backdrop}")`}}/><div className="dc-cinema-vignette"/><div className="dc-cinema-grain"/>
      <div className="dc-cinema-hero-inner">
        <div className="dc-cinema-copy">
          <div className="dc-cinema-eyebrow"><span/> YOUR NEXT GREAT WATCH STARTS HERE</div>
          <h1>Stories for<br/>every <em>side of you.</em></h1>
          <p className="dc-cinema-lede">A smarter way to find your next favourite film. Discover stories that match your taste, your mood, and the moments you're in.</p>
          <form className="dc-cinema-search" onSubmit={handleSearch}><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search movies, genres, or moods" aria-label="Search movies"/><button type="submit" disabled={searching}>{searching?"Searching…":"Explore"} <ArrowRight size={15}/></button></form>
          <div className="dc-cinema-hero-ctas"><Link to="/signup" className="dc-cinema-primary"><Sparkles size={16}/> Find my next film</Link><a href="#how-it-works" className="dc-cinema-secondary"><Play size={15}/> See how it works</a></div>
          <div className="dc-cinema-proof"><div className="dc-proof-avatars"><span>D</span><span>C</span><span>+</span></div><p><strong>Made around your taste</strong><small>Not another endless list of movies</small></p></div>
        </div>
        <div className="dc-cinema-showcase" aria-label="Preview of the DeepCine movie discovery experience">
          <div className="dc-showcase-window">
            <div className="dc-showcase-topbar"><span className="dc-showcase-logo">Deep<span>Cine</span></span><div className="dc-showcase-links"><span>For you</span><span>Movies</span><span>Discover</span><span>My list</span></div><span className="dc-showcase-avatar">D</span></div>
            <div className="dc-showcase-feature" style={{backgroundImage:`linear-gradient(90deg,rgba(4,13,20,.94),rgba(4,13,20,.4) 65%,rgba(4,13,20,.1)),linear-gradient(0deg,#08141d,transparent 55%),url("${backdrop}")`}}>
              <span className="dc-showcase-label"><i/> TONIGHT'S FEATURED STORY</span><h2>{featured?.title||"Find your next story"}</h2><p>{featured?.overview||"Discover films chosen around the things you love."}</p>
              <div className="dc-showcase-feature-meta">{featured?.vote_average?<span><Star size={12} fill="currentColor"/> {Number(featured.vote_average).toFixed(1)}</span>:<span>PERSONALISED DISCOVERY</span>}<span>CURATED FOR YOU</span></div>
              <Link to="/signup" className="dc-showcase-play"><Play size={13} fill="currentColor"/> Explore film</Link>
            </div>
            <div className="dc-showcase-rail-heading"><span>Trending discoveries</span><small>EXPLORE ALL ↗</small></div>
            <div className="dc-showcase-posters">{preview.length?preview.map(m=><Link to={`/movie/${m.id}`} key={m.id} className="dc-showcase-poster" title={m.title}><img src={posterOf(m)} alt={m.title} loading="lazy"/><span>{m.title}</span></Link>):[1,2,3,4,5,6].map(n=><div className="dc-showcase-poster-placeholder" key={n}/>)}</div>
            <div className="dc-showcase-foot"><span><WandSparkles size={12}/> Recommendations shaped by your taste</span><span>DEEPCINE / 01</span></div>
          </div>
          <div className="dc-showcase-float dc-showcase-float-top"><span className="dc-float-icon"><Sparkles size={15}/></span><span><b>Made for your taste</b><small>Personalised discovery</small></span></div>
          <div className="dc-showcase-float dc-showcase-float-bottom"><span className="dc-float-rating"><Star size={14} fill="currentColor"/></span><span><b>More than popular</b><small>Find films you'll actually love</small></span></div>
        </div>
      </div>
      <a className="dc-cinema-scroll" href="#how-it-works"><span>SCROLL TO EXPLORE</span><ArrowDown size={14}/></a>
    </section>
    <section className="dc-cinema-benefits" id="how-it-works">
      <div className="dc-benefit"><span><WandSparkles size={19}/></span><div><strong>Personalised picks</strong><small>Discover films shaped around your taste</small></div></div>
      <div className="dc-benefit"><span><Compass size={19}/></span><div><strong>Explore by mood</strong><small>Find the right story for right now</small></div></div>
      <div className="dc-benefit"><span><BookmarkPlus size={19}/></span><div><strong>Your own collection</strong><small>Save films and build your watchlist</small></div></div>
      <div className="dc-benefit"><span><Users size={19}/></span><div><strong>More ways to discover</strong><small>Explore recommendations from patterns in taste</small></div></div>
    </section>
    <div className="dc-cinema-trending" id="trending"><div className="dc-cinema-section-intro"><div><span>THE CINEMA NEVER STOPS</span><h2>Stories worth discovering<span>.</span></h2></div><Link to="/discover">Explore the collection <ArrowRight size={15}/></Link></div><TrendingMarquee movies={movies} loading={loading}/></div>
    <section className="dc-cinema-bottom-cta"><div><span>YOUR NEXT FAVOURITE IS OUT THERE</span><h2>Let your next story find you.</h2><p>Build your taste profile and make movie night easier.</p></div><Link to="/signup">Start discovering <ArrowRight size={16}/></Link></section>
    <footer className="dc-cinema-footer"><Link to="/" className="dc-cinema-brand"><span className="dc-brand-mark"><Clapperboard size={16}/></span><span>Deep<span>Cine</span></span></Link><span>DISCOVER BETTER. WATCH HAPPIER.</span><small>© {new Date().getFullYear()} DeepCine</small></footer>
  </main>;
}
