import { useEffect,useState } from "react";
import { useLocation,useNavigate } from "react-router-dom";
import { Sparkles,SlidersHorizontal } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import HomeSidebar from "../components/layout/HomeSidebar";
import RecommendationSection from "../components/RecommendationSection";
import { getAuthState } from "../services/auth";
import { getTrendingMovies,getRecommendations,getCollaborativeRecommendations,getPersonalizedRecommendations,getCoWatchRecommendations,discoverMovies } from "../services/movies";
export default function RecommendPage(){
 const location=useLocation(),navigate=useNavigate(),{userId}=getAuthState();
 const search=location.state?.search?.trim()||"",filters=location.state?.filters||null;
 const [recommended,setRecommended]=useState([]),[personalized,setPersonalized]=useState([]),[collaborative,setCollaborative]=useState([]),[coWatch,setCoWatch]=useState([]),[filterPicks,setFilterPicks]=useState([]),[trending,setTrending]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 useEffect(()=>{let cancelled=false;async function load(){setLoading(true);setError("");try{
 const [s,p,c,w,t,f]=await Promise.all([search?getRecommendations(search):Promise.resolve([]),userId?getPersonalizedRecommendations(userId):Promise.resolve([]),userId?getCollaborativeRecommendations(userId):Promise.resolve([]),userId?getCoWatchRecommendations(userId):Promise.resolve([]),getTrendingMovies(),filters?discoverMovies({mood:filters.mood,genres:filters.genres||[],language:filters.language,sortBy:filters.sortBy,page:1}):Promise.resolve([])]);
 if(cancelled)return;setRecommended(s||[]);setPersonalized(p||[]);setCollaborative(c||[]);setCoWatch(w||[]);setTrending(t||[]);setFilterPicks(f||[]);
 }catch(err){console.error("AI Picks load failed",err);if(!cancelled)setError("Some recommendations couldn't be loaded. Please try again.");}finally{if(!cancelled)setLoading(false);}}
 load();return()=>{cancelled=true;};},[search,userId,filters]);
 const hasPersonalSignals=Boolean(search||filters||personalized.length||collaborative.length||coWatch.length);
 return <div className="dc-app-shell"><HomeSidebar/><main className="dc-app-main"><Navbar/><div className="dc-ai-page">
 <section className="dc-ai-intro"><span className="dc-discover-kicker"><Sparkles size={13}/> DEEPCINE INTELLIGENCE</span><h1>Your next watch, <em>thoughtfully picked.</em></h1><p>Movie picks shaped by what you search, what you rate and the genres you explore. Use the search icon in the top bar or build a mix in Explore.</p><div className="dc-ai-shortcuts"><button onClick={()=>navigate("/discover")}><SlidersHorizontal size={14}/> Build a genre mix</button>{search&&<span className="dc-ai-context">Search signal: “{search}”</span>}{filters&&<span className="dc-ai-context">Your Explore filters are applied</span>}</div></section>
 {error&&<p className="dc-ai-error">{error}</p>}
 {search&&<RecommendationSection movies={recommended} loading={loading} eyebrow="BASED ON YOUR SEARCH" title={`Because you searched “${search}”`} description="Content-based matches related to the title you searched for." emptyMessage="No close matches found. Try another title from the top-bar search."/>}
 {filters&&<RecommendationSection movies={filterPicks} loading={loading} eyebrow="BASED ON YOUR EXPLORE FILTERS" title="Your selected movie mix" description="Movies matching the mood, genres and language you selected in Explore." emptyMessage="No films matched those filters. Adjust your selection in Explore."/>}
 {userId&&<RecommendationSection movies={personalized} loading={loading} eyebrow="LEARNED FROM YOUR TASTE" title="Picked for you" description="Personalized from your recorded movie activity and preferences." emptyMessage="Rate movies, add titles to your watchlist and explore films. Your personal picks will appear here as the system learns your taste."/>}
 {userId&&<RecommendationSection movies={coWatch} loading={loading} eyebrow="COMMUNITY DISCOVERY" title="Viewers who explored similar films" description="Movies opened by other users who also opened titles in your history. Each viewer contributes once per movie." emptyMessage="More community activity is needed before co-view recommendations become available."/>}
 {userId&&<RecommendationSection movies={collaborative} loading={loading} eyebrow="COLLABORATIVE FILTERING" title="Latent-factor picks" description="Recommendations from the trained implicit-feedback ALS model." emptyMessage="The collaborative model is unavailable or does not yet have enough interaction data."/>}
 {!hasPersonalSignals&&<div className="dc-ai-fallback"><span className="dc-discover-step">START EXPLORING</span><h2>Popular right now</h2><p>Until DeepCine has enough signals to personalize your picks, here's what's trending.</p></div>}
 <RecommendationSection movies={trending} loading={loading} eyebrow={hasPersonalSignals?"A LITTLE INSPIRATION":"TRENDING NOW"} title={hasPersonalSignals?"Trending for everyone":"Popular right now"} description="Currently popular films, useful when you just want something good to watch." emptyMessage="Trending movies are temporarily unavailable."/>
 <footer className="dc-ai-footer">DEEPCINE · RECOMMENDATIONS THAT LEARN YOUR TASTE</footer>
 </div></main></div>;
}