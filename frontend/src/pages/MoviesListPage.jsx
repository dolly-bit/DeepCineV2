import { useEffect,useState } from "react";
import { useLocation,useNavigate } from "react-router-dom";
import { ChevronLeft,LoaderCircle } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import HomeSidebar from "../components/layout/HomeSidebar";
import MovieCard from "../components/home/MovieCard";
import { discoverMovies,getPersonalizedRecommendations,getCollaborativeRecommendations } from "../services/movies";
export default function MoviesListPage(){
  const location=useLocation(),navigate=useNavigate();
  const mode=location.state?.mode||"trending",title=location.state?.title||"Movies";
  const [movies,setMovies]=useState([]),[page,setPage]=useState(0),[loading,setLoading]=useState(true),[loadingMore,setLoadingMore]=useState(false),[hasMore,setHasMore]=useState(true),[error,setError]=useState("");
  useEffect(()=>{
    let cancelled=false;
    async function load(){
      setLoading(true);setError("");setMovies([]);setPage(0);setHasMore(true);
      try{
        if(mode==="recommended"||mode==="collaborative"){
          const id=localStorage.getItem("user_id");
          const result=!id?[]:mode==="recommended"?await getPersonalizedRecommendations(id):await getCollaborativeRecommendations(id);
          if(!cancelled){setMovies(result||[]);setHasMore(false);} return;
        }
        const sortBy=mode==="top-rated"?"vote_average.desc":mode==="upcoming"?"primary_release_date.asc":"popularity.desc";
        const batches=await Promise.all([1,2,3,4,5].map(page=>discoverMovies({sortBy,page})));
        if(cancelled)return;
        const unique=new Map();batches.flat().forEach(m=>{if(m.id&&!unique.has(m.id))unique.set(m.id,m);});
        setMovies([...unique.values()]);setPage(5);setHasMore(unique.size>=100);
      }catch(e){console.error(e);if(!cancelled)setError("Unable to load this movie collection.");}
      finally{if(!cancelled)setLoading(false);}
    }
    load();return()=>{cancelled=true;};
  },[mode]);
  async function loadMore(){
    if(loadingMore||!hasMore)return;setLoadingMore(true);setError("");
    try{
      const sortBy=mode==="top-rated"?"vote_average.desc":mode==="upcoming"?"primary_release_date.asc":"popularity.desc";
      const batches=await Promise.all([1,2,3,4,5].map(offset=>discoverMovies({sortBy,page:page+offset})));
      const known=new Set(movies.map(m=>m.id));const additions=batches.flat().filter(m=>m.id&&!known.has(m.id));
      setMovies(old=>[...old,...additions]);setPage(old=>old+5);setHasMore(additions.length>0&&page<495);
    }catch(e){console.error(e);setError("More films could not be loaded. Please retry.");}
    finally{setLoadingMore(false);}
  }
  return <div className="dc-app-shell"><HomeSidebar/><main className="dc-app-main"><Navbar/><section className="dc-catalog-page">
    <button className="dc-catalog-back" onClick={()=>navigate("/home")}><ChevronLeft size={16}/> Back to home</button>
    <div className="dc-catalog-heading"><div><span className="dc-slider-eyebrow">THE DEEPCINE LIBRARY</span><h1>{title}</h1><p>Explore a larger collection. Each batch adds up to 100 more films.</p></div><span className="dc-catalog-count">{movies.length.toLocaleString()} FILMS LOADED</span></div>
    {loading?<div className="dc-catalog-grid">{Array.from({length:20}).map((_,i)=><div className="dc-catalog-skeleton" key={i}/>)}</div>:error&&!movies.length?<p className="dc-catalog-message">{error}</p>:!movies.length?<p className="dc-catalog-message">No movies are available for this collection.</p>:<>
      <div className="dc-catalog-grid">{movies.map(movie=><MovieCard key={movie.id} movie={movie}/>)}</div>
      {error&&<p className="dc-catalog-message">{error}</p>}
      {hasMore?<div className="dc-catalog-load-wrap"><button className="dc-catalog-load" onClick={loadMore} disabled={loadingMore}>{loadingMore?<><LoaderCircle size={16} className="animate-spin"/> Loading...</>:"Load 100 more movies"}</button></div>:<p className="dc-catalog-end">You've reached the end of this collection.</p>}
    </>}
  </section></main></div>;
}