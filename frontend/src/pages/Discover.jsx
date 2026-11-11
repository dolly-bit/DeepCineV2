import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { SlidersHorizontal, Sparkles, X, RotateCcw, Film, Languages, Clapperboard, ChevronDown } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import HomeSidebar from "../components/layout/HomeSidebar";
import MovieCard from "../components/home/MovieCard";
import { getMoods, getGenres, getLanguages, discoverMovies } from "../services/movies";

const MOOD_META = {
  feel_good: { icon: "☀", note: "Warm, uplifting and easy to love", color: "gold" },
  intense: { icon: "⚡", note: "High stakes. No slow moments.", color: "red" },
  romantic: { icon: "♡", note: "Chemistry, connection and longing", color: "rose" },
  scary: { icon: "☾", note: "Dark stories and edge-of-seat tension", color: "violet" },
  mind_bending: { icon: "◈", note: "Twists that stay with you", color: "blue" },
  emotional: { icon: "✦", note: "Stories that hit somewhere deep", color: "pink" },
  chill: { icon: "〰", note: "A slower pace for a quieter night", color: "green" },
  epic_adventure: { icon: "✧", note: "Big worlds and bigger journeys", color: "cyan" },
};

export default function Discover() {
  const navigate=useNavigate(), location=useLocation();
  const [moods,setMoods]=useState([]),[genres,setGenres]=useState([]),[languages,setLanguages]=useState([]);
  const [activeMood,setActiveMood]=useState(location.state?.mood||null);
  const [activeGenres,setActiveGenres]=useState(location.state?.genreId?[location.state.genreId]:[]);
  const [activeLanguage,setActiveLanguage]=useState(null),[sortBy,setSortBy]=useState("popularity.desc");
  const [movies,setMovies]=useState([]),[page,setPage]=useState(1),[hasMore,setHasMore]=useState(true);
  const [loading,setLoading]=useState(true),[loadingFilters,setLoadingFilters]=useState(true),[error,setError]=useState("");

  useEffect(()=>{
    let cancelled=false;
    Promise.all([getMoods(),getGenres(),getLanguages()]).then(([m,g,l])=>{
      if(cancelled)return;setMoods(m||[]);setGenres(g||[]);setLanguages(l||[]);
    }).catch(err=>console.error("Discovery filters failed",err)).finally(()=>{if(!cancelled)setLoadingFilters(false);});
    return()=>{cancelled=true;};
  },[]);

  useEffect(()=>{
    setPage(1);setMovies([]);setHasMore(true);setError("");
  },[activeMood,activeGenres,activeLanguage,sortBy]);

  useEffect(()=>{
    let cancelled=false;
    async function search(){
      setLoading(true);setError("");
      try{
        const data=await discoverMovies({mood:activeMood,genres:activeGenres,language:activeLanguage,sortBy,page});
        if(cancelled)return;
        setMovies(previous=>page===1?data:[...previous,...data]);
        setHasMore(data.length===20&&page<500);
        if(page===1&&!data.length)setError("No titles matched this combination. Try changing one of your picks.");
      }catch(err){console.error(err);if(!cancelled){setError("We couldn't load this selection. Please try again.");setHasMore(false);}}
      finally{if(!cancelled)setLoading(false);}
    }
    search();return()=>{cancelled=true;};
  },[activeMood,activeGenres,activeLanguage,sortBy,page]);

  const toggleGenre=id=>setActiveGenres(current=>current.includes(id)?current.filter(value=>value!==id):[...current,id]);
  const clearAll=()=>{setActiveMood(null);setActiveGenres([]);setActiveLanguage(null);setSortBy("popularity.desc");};
  const activeGenreNames=useMemo(()=>genres.filter(g=>activeGenres.includes(g.id)).map(g=>g.name),[genres,activeGenres]);
  const selectionCount=(activeMood?1:0)+activeGenres.length+(activeLanguage?1:0);
  const selectedMood=moods.find(m=>m.key===activeMood);

  return <div className="dc-app-shell">
    <HomeSidebar/>
    <main className="dc-app-main">
      <Navbar/>
      <div className="dc-discover-page">
        <section className="dc-discover-intro">
          <div><span className="dc-discover-kicker"><Sparkles size={13}/> YOUR NEXT GREAT WATCH STARTS HERE</span>
            <h1>What are we <em>watching</em> tonight?</h1>
            <p>Build your own movie mood. Pick a feeling, mix genres, choose a language — DeepCine will shape the collection.</p>
          </div>
          <div className="dc-discover-stamp"><span>01</span><small>SET YOUR<br/>VIBE</small></div>
        </section>

        <section className="dc-discover-builder">
          <div className="dc-builder-heading"><div><span className="dc-discover-step">STEP 01 / THE FEELING</span><h2>Choose your mood</h2><p>Start with the kind of night you want.</p></div><span className="dc-builder-optional">PICK ONE</span></div>
          <div className="dc-mood-picker">
            {moods.map(m=>{const meta=MOOD_META[m.key]||{icon:"✦",note:m.description||"Explore this mood",color:"cyan"};return <button key={m.key} title={m.description} onClick={()=>setActiveMood(current=>current===m.key?null:m.key)} className={`dc-mood-choice tone-${meta.color}${activeMood===m.key?" chosen":""}`} aria-pressed={activeMood===m.key}>
              <span className="dc-mood-icon">{meta.icon}</span><span className="dc-mood-name">{m.label}</span><span className="dc-mood-note">{meta.note}</span><span className="dc-mood-check">{activeMood===m.key?"✓":"＋"}</span>
            </button>;})}
            {loadingFilters&&Array.from({length:8}).map((_,i)=><div className="dc-mood-loading" key={i}/>)}
          </div>

          <div className="dc-builder-divider"/>
          <div className="dc-builder-heading"><div><span className="dc-discover-step">STEP 02 / THE FLAVOUR</span><h2>Mix your genres</h2><p>Choose more than one. Unexpected combinations are welcome.</p></div><span className="dc-builder-optional">MULTI-SELECT</span></div>
          <div className="dc-genre-picker">
            {genres.map(g=><button key={g.id} onClick={()=>toggleGenre(g.id)} className={`dc-genre-chip${activeGenres.includes(g.id)?" selected":""}`} aria-pressed={activeGenres.includes(g.id)}><span>{activeGenres.includes(g.id)?"✓":"＋"}</span>{g.name}</button>)}
            {loadingFilters&&Array.from({length:8}).map((_,i)=><div className="dc-genre-loading" key={i}/>)}
          </div>

          <div className="dc-builder-divider"/>
          <div className="dc-builder-heading dc-preference-heading"><div><span className="dc-discover-step">STEP 03 / MAKE IT YOURS</span><h2>Fine-tune the evening</h2><p>A couple of details to narrow the search.</p></div></div>
          <div className="dc-preference-row">
            <label className="dc-preference-control"><span><Languages size={15}/> Language</span><select value={activeLanguage||""} onChange={e=>setActiveLanguage(e.target.value||null)}><option value="">Any language</option>{languages.map(l=><option key={l.code} value={l.code}>{l.label}</option>)}</select><ChevronDown size={14}/></label>
            <label className="dc-preference-control"><span><Clapperboard size={15}/> Sort collection</span><select value={sortBy} onChange={e=>setSortBy(e.target.value)}><option value="popularity.desc">Most popular</option><option value="vote_average.desc">Highest rated</option><option value="primary_release_date.desc">Newest releases</option><option value="revenue.desc">Biggest hits</option></select><ChevronDown size={14}/></label>
          </div>

          <div className="dc-selection-summary">
            <div className="dc-selection-copy"><span className="dc-summary-icon"><Film size={16}/></span><div><strong>{selectionCount?selectionCount+" preferences selected":"Your movie mix is wide open"}</strong><small>{[selectedMood?.label,...activeGenreNames,activeLanguage?languages.find(l=>l.code===activeLanguage)?.label:null].filter(Boolean).join(" · ")||"Choose a mood or genre to make this collection yours."}</small></div></div>
            {selectionCount>0&&<button onClick={clearAll} className="dc-clear-selection"><RotateCcw size={13}/> Reset picks</button>}
          </div>
        </section>

        <section className="dc-discover-results">
          <div className="dc-results-heading"><div><span className="dc-discover-step">MADE FOR YOUR MOOD</span><h2>{selectedMood?selectedMood.label+" movies":activeGenreNames.length?activeGenreNames.join(" + "):"Explore the collection"}</h2><p>{movies.length?movies.length+" films in this view":"Your results update when you change your picks."}</p></div><span className="dc-results-sort"><SlidersHorizontal size={14}/> {sortBy==="vote_average.desc"?"Top rated":sortBy==="primary_release_date.desc"?"Newest first":sortBy==="revenue.desc"?"Box office":"Popular first"}</span></div>
          {loading&&page===1?<div className="dc-discover-grid">{Array.from({length:12}).map((_,i)=><div className="dc-discover-skeleton" key={i}/>)}</div>:
            movies.length===0?<div className="dc-discover-empty"><span><Sparkles size={22}/></span><h3>{error||"A blank canvas for your next favourite."}</h3><p>Try another mood or remove a genre to widen your results.</p><button onClick={clearAll}>Explore everything</button></div>:
            <><div className="dc-discover-grid">{movies.map(movie=><div key={movie.id} className="dc-discover-movie" onClick={()=>navigate(`/movie/${movie.id}`)}><MovieCard movie={movie}/></div>)}</div>
            {hasMore&&<div className="dc-discover-more"><button onClick={()=>setPage(value=>value+1)} disabled={loading}>{loading?"Finding more films":"Load more films"}</button></div>}</>}
        </section>
      </div>
    </main>
  </div>;
}