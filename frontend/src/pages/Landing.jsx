import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, BookmarkPlus, Clapperboard, Download, Film, MonitorSmartphone, Play, Search, Sparkles, Star, Users, WandSparkles } from "lucide-react";
import { getTrendingMovies, recordSearch, searchMovies } from "../services/movies";
import "./Landing.css";

const posterOf = (m) => m?.poster_url || (m?.poster_path ? `https://image.tmdb.org/t/p/w500${m.poster_path}` : "");
const backdropOf = (m) => m?.backdrop_url || (m?.backdrop_path ? `https://image.tmdb.org/t/p/original${m.backdrop_path}` : "");

export default function Landing() {
  const [movies,setMovies]=useState([]),[query,setQuery]=useState(""),[searching,setSearching]=useState(false);
  const navigate=useNavigate();
  useEffect(()=>{let active=true;getTrendingMovies().then(data=>{if(active)setMovies(Array.isArray(data)?data:[])}).catch(err=>console.error("Unable to load trending movies:",err));return()=>{active=false}},[]);
  const featured=useMemo(()=>movies.find(m=>backdropOf(m)&&posterOf(m))||movies.find(m=>posterOf(m))||null,[movies]);
  const backdrop=backdropOf(featured)||"https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg";
  const ambientBackdrop=backdropOf(movies.find(m=>m.id!==featured?.id&&backdropOf(m)))||backdrop;
  const preview=movies.filter(m=>posterOf(m)).slice(0,6);
  async function handleSearch(e){e.preventDefault();const term=query.trim();if(!term||searching)return;setSearching(true);recordSearch(term);try{const results=await searchMovies(term);navigate("/recommend",{state:{search:term,movies:results}})}catch(err){console.error("Movie search failed:",err);navigate("/recommend",{state:{search:term}})}finally{setSearching(false)}}
  return <main className="dc-cinema-landing dc-reference-landing">
    <header className="dc-cinema-header">
      <Link to="/" className="dc-cinema-brand"><span className="dc-brand-mark"><Clapperboard size={19}/></span><span>Deep<span>Cine</span></span></Link>
      
      <div className="dc-cinema-account"><Link to="/login" className="dc-cinema-signin">Sign in</Link><Link to="/signup" className="dc-cinema-join">Start discovering <ArrowRight size={14}/></Link></div>
    </header>

    <section className="dc-cinema-hero dc-reference-hero" id="discover">
      <div className="dc-cinema-backdrop" style={{backgroundImage:`url("${backdrop}")`}}/><div className="dc-cinema-vignette"/><div className="dc-cinema-grain"/>
      <div className="dc-reference-stage">
        <div className="dc-reference-copy">
          <div className="dc-cinema-eyebrow"><span/> A BETTER WAY TO FIND YOUR NEXT FILM</div>
          <h1>Stories<br/>for Every<br/><em>Mood.</em></h1>
          <p className="dc-reference-subtitle">Films worth finding. Stories worth remembering.</p>
          <div className="dc-reference-perks">
            <div><span><Play size={18}/></span><p><b>Discover your next favourite</b><small>Personalised movie recommendations</small></p></div>
            <div><span><MonitorSmartphone size={18}/></span><p><b>Explore every kind of story</b><small>Browse by genre, mood and taste</small></p></div>
            <div><span><Users size={18}/></span><p><b>Your taste, your collection</b><small>Build a watchlist that feels like you</small></p></div>
            <div><span><Download size={18}/></span><p><b>Less searching, more watching</b><small>Find films worth your time</small></p></div>
          </div>
          <form className="dc-cinema-search dc-reference-search" onSubmit={handleSearch}><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Find a movie or genre" aria-label="Search movies"/><button type="submit" disabled={searching}>{searching?"…":"Search"} <ArrowRight size={14}/></button></form>
          <Link to="/signup" className="dc-reference-cta"><Sparkles size={15}/> Create your free account</Link>
        </div>

        <div className="dc-reference-devices">
          <div className="dc-reference-screen">
            <div className="dc-reference-screen-top">
              <span className="dc-screen-logo">Deep<span>Cine</span></span>
              <div className="dc-screen-nav"><span className="active">Home</span><span>Movies</span><span>Discover</span><span>My List</span></div>
              <div className="dc-screen-tools"><Search size={12}/><span className="dc-screen-user">D</span></div>
            </div>
            <div className="dc-reference-screen-hero" style={{backgroundImage:`linear-gradient(90deg,rgba(3,12,19,.96),rgba(3,12,19,.58) 52%,rgba(3,12,19,.05)),linear-gradient(0deg,#07131c,transparent 58%),url("${backdrop}")`}}>
              <span className="dc-screen-kicker">✦ FEATURED FOR YOU</span>
              <h2>{featured?.title||"Beyond the ordinary"}</h2>
              <p>{featured?.overview||"Discover stories you'll want to come back to."}</p>
              <div className="dc-screen-meta">{featured?.vote_average?<span><Star size={11} fill="currentColor"/> {Number(featured.vote_average).toFixed(1)}</span>:<span>PERSONALISED PICK</span>}<span>RECOMMENDED FOR YOU</span></div>
              <Link to="/signup" className="dc-screen-watch"><Play size={11} fill="currentColor"/> Explore now</Link>
            </div>
            <div className="dc-screen-row-title"><b>Trending now</b><span>VIEW ALL ↗</span></div>
            <div className="dc-screen-posters">{preview.length?preview.map(m=><Link to={`/movie/${m.id}`} key={m.id} title={m.title}><img src={posterOf(m)} alt={m.title} loading="lazy"/><small>{m.title}</small></Link>):[1,2,3,4,5,6].map(n=><div className="dc-screen-poster-placeholder" key={n}/>)}</div>
            <div className="dc-screen-row-title dc-screen-second-title"><b>Picked around your taste</b><span>PERSONALISED ✦</span></div>
            <div className="dc-screen-second-row">{preview.slice(0,4).map((m,i)=><Link to={`/movie/${m.id}`} key={m.id}><img src={posterOf(m)} alt="" loading="lazy"/><span>{i%2===0?"Because you watched":"You might enjoy"}</span></Link>)}</div>
          </div>

          <div className="dc-reference-tablet">
            <div className="dc-device-top"><span>Deep<span>Cine</span></span><Search size={10}/><span>•••</span></div>
            <div className="dc-tablet-feature" style={{backgroundImage:`linear-gradient(0deg,#08151e,transparent),url("${backdrop}")`}}><span>FEATURED FILM</span><b>{featured?.title||"A brighter tomorrow"}</b><i><Play size={10}/></i></div>
            <div className="dc-device-caption">Continue discovering</div>
            <div className="dc-tablet-posters">{preview.slice(0,3).map(m=><img key={m.id} src={posterOf(m)} alt="" loading="lazy"/>)}</div>
            <div className="dc-device-caption">Your watchlist</div>
            <div className="dc-tablet-posters">{preview.slice(3,6).map(m=><img key={m.id} src={posterOf(m)} alt="" loading="lazy"/>)}</div>
          </div>

          <div className="dc-reference-phone">
            <div className="dc-phone-notch"/>
            <div className="dc-phone-brand">Deep<span>Cine</span><Search size={10}/></div>
            <div className="dc-phone-feature" style={{backgroundImage:`linear-gradient(0deg,#06131c,transparent),url("${backdrop}")`}}><small>FOR YOUR NEXT MOVIE NIGHT</small><b>{featured?.title||"Find your story"}</b></div>
            <span className="dc-phone-label">Browse by genre</span>
            <div className="dc-phone-genres"><span>Action</span><span>Drama</span><span>Comedy</span><span>Thriller</span></div>
            <div className="dc-phone-label">Picked for you</div>
            <div className="dc-phone-picks">{preview.slice(0,2).map(m=><img key={m.id} src={posterOf(m)} alt="" loading="lazy"/>)}</div>
            <div className="dc-phone-nav"><span>⌂</span><span>⌕</span><span>♡</span><span>◉</span></div>
          </div>
          <div className="dc-reference-note"><WandSparkles size={13}/><span><b>Recommendations with a reason</b><small>Discover beyond the popular picks</small></span></div>
        </div>
      </div>

      <div className="dc-reference-ribbon" id="how-it-works">
        <div><span><Film size={18}/></span><p><b>Personalised picks</b><small>Chosen around your taste</small></p></div>
        <div><span><BookmarkPlus size={18}/></span><p><b>Thousands of titles</b><small>Explore your next favourite</small></p></div>
        <div><span><Sparkles size={18}/></span><p><b>Discover more</b><small>Find stories beyond the obvious</small></p></div>
        <div className="dc-ribbon-action"><Link to="/signup">Start discovering <ArrowRight size={14}/></Link></div>
      </div>
    </section>
  </main>;
}
