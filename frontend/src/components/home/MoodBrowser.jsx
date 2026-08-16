import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { getMoods } from "../../services/movies";

// Each mood gets its own gradient + glow color so the section feels
// alive and distinct per-mood, rather than a flat repeated card style.
const MOOD_STYLES = {
  feel_good: "from-amber-400/25 via-amber-300/10 to-transparent hover:shadow-amber-400/30",
  intense: "from-red-500/25 via-orange-400/10 to-transparent hover:shadow-red-500/30",
  romantic: "from-pink-500/25 via-rose-300/10 to-transparent hover:shadow-pink-500/30",
  scary: "from-purple-900/40 via-violet-700/15 to-transparent hover:shadow-purple-700/40",
  mind_bending: "from-cyan-400/25 via-blue-400/10 to-transparent hover:shadow-cyan-400/30",
  emotional: "from-indigo-400/25 via-blue-300/10 to-transparent hover:shadow-indigo-400/30",
  chill: "from-emerald-400/25 via-teal-300/10 to-transparent hover:shadow-emerald-400/30",
  epic_adventure: "from-fuchsia-500/25 via-purple-400/10 to-transparent hover:shadow-fuchsia-500/30",
};

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 18, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.4, ease: "easeOut" },
  },
};

export default function MoodBrowser() {
  const navigate = useNavigate();
  const [moods, setMoods] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getMoods();
        setMoods(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (!loading && moods.length === 0) return null;

  return (
    <section className="max-w-7xl mx-auto px-6 mt-14">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cm-purple mb-1">
            In the mood for...
          </p>
          <h2 className="text-xl font-bold text-white">
            Browse by mood
          </h2>
        </div>

        <button
          onClick={() => navigate("/discover")}
          className="flex items-center gap-1.5 text-sm font-medium text-cm-purple transition hover:text-cm-violet"
        >
          See all filters
          <ArrowRight size={15} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-2xl bg-white/5" />
          ))}
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          className="grid grid-cols-2 gap-3 sm:grid-cols-4"
        >
          {moods.map((mood) => (
            <motion.button
              key={mood.key}
              variants={cardVariants}
              whileHover={{ y: -4, scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate("/discover", { state: { mood: mood.key } })}
              title={mood.description}
              className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${
                MOOD_STYLES[mood.key] || "from-white/10 to-transparent"
              } p-4 text-left shadow-lg transition-shadow duration-300`}
            >
              <div className="pointer-events-none absolute -right-4 -top-4 h-16 w-16 rounded-full bg-white/10 blur-2xl transition-opacity duration-300 group-hover:opacity-80" />
              <p className="text-lg font-semibold text-white">
                {mood.label}
              </p>
              <p className="mt-1 text-xs leading-snug text-slate-300 line-clamp-2">
                {mood.description}
              </p>
            </motion.button>
          ))}
        </motion.div>
      )}
    </section>
  );
}