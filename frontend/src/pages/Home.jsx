import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import HomeSidebar from "../components/layout/HomeSidebar";
import DashboardHero from "../components/home/DashboardHero";
import MovieSlider from "../components/home/MovieSlider";
import PersonalizedMovies from "../components/PersonalizedMovies";
import CollaborativeMovies from "../components/CollaborativeMovies";
import { getTrendingMovies, getTopRatedMovies, getUpcomingMovies, getGenres } from "../services/movies";

function futureOnly(movies) {
  const today = new Date(); today.setHours(0,0,0,0);
  return movies.filter(m => m.release_date && new Date(m.release_date) >= today).sort((a,b)=>new Date(a.release_date)-new Date(b.release_date));
}
function Categories({ genres, loading }) {
  const navigate = (genre) => window.dispatchEvent(new CustomEvent("deepcine:genre", { detail: genre }));
  return <aside className="dc-category-panel">
    <div className="dc-category-heading"><h2>Categories</h2><span>Browse genres</span></div>
    {loading ? <div className="dc-category-grid">{Array.from({length:8}).map((_,i)=><div className="dc-category-skeleton" key={i}/>)}</div> :
      <div className="dc-category-grid">{genres.slice(0,8).map((g,i)=><button key={g.id} className={"dc-category-tile dc-category-"+i} onClick={()=>navigate(g)}><span>{g.name}</span></button>)}</div>}
    <a className="dc-category-all" href="/discover">View all genres <span>→</span></a>
  </aside>;
}
export default function Home() {
  const [trending,setTrending]=useState([]), [topRated,setTopRated]=useState([]), [upcoming,setUpcoming]=useState([]), [genres,setGenres]=useState([]);
  const [loading,setLoading]=useState(true), [genresLoading,setGenresLoading]=useState(true);
  useEffect(()=>{
    let cancelled=false;
    Promise.all([getTrendingMovies(),getTopRatedMovies(),getUpcomingMovies(),getGenres()]).then(([t,r,u,g])=>{
      if(cancelled)return; setTrending(t||[]);setTopRated(r||[]);setUpcoming(futureOnly(u||[]));setGenres(g||[]);
    }).catch(err=>console.error("Home data load failed",err)).finally(()=>{if(!cancelled){setLoading(false);setGenresLoading(false);}});
    return ()=>{cancelled=true;};
  },[]);
  return <div className="dc-app-shell">
    <HomeSidebar/>
    <main className="dc-app-main">
      <Navbar/>
      <div className="dc-home-dashboard">
        <div className="dc-home-feature-layout"><DashboardHero movies={trending}/><Categories genres={genres} loading={genresLoading}/></div>
        <MovieSlider title="Trending Now" movies={trending} loading={loading} seeMoreState={{mode:"trending",title:"Trending Now"}}/>
        <PersonalizedMovies/>
        <CollaborativeMovies/>
        <MovieSlider title="Top Rated" movies={topRated} loading={loading} seeMoreState={{mode:"top-rated",title:"Top Rated"}}/>
        <MovieSlider title="Coming Soon" movies={upcoming} loading={loading} seeMoreState={{mode:"upcoming",title:"Coming Soon"}}/>
      </div>
      <footer className="dc-home-footer"><span>DEEPCINE</span><span>DISCOVER SOMETHING WORTH WATCHING.</span></footer>
    </main>
  </div>;
}