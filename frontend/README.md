# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# DeepCine
## Setup — Tailwind CSS version

```bash
npm install -D tailwindcss postcss autoprefixer
npm install lucide-react
```
Copy `tailwind.config.js`, `postcss.config.js`, and everything in `src/` into your project.
Make sure `src/index.css` (which contains the `@tailwind` directives) is imported once at your app root — it's already imported in `App.jsx`.

## Structure
```
tailwind.config.js     -> CineMind purple/black palette, fonts, custom keyframes/animations
postcss.config.js
src/
  index.css             -> @tailwind directives + font import + scrollbar-hide utility
  data/movies.js         -> hero slides + all 5 row datasets + filter options
  components/
    TopBar.jsx             -> logo, notifications, profile dropdown
    HeroCarousel.jsx         -> auto-advancing banner (5s interval, dot nav)
    FilterBar.jsx              -> greeting + Genre/Mood/Language + search
    MovieRow.jsx                -> horizontal scroll row w/ arrow controls
    PosterCard.jsx                -> single movie card
  pages/RecommendPage.jsx    -> assembles the full dashboard
  App.jsx                  -> entry point
```

## Notes
- All custom colors live under the `cm` namespace in `tailwind.config.js` (e.g. `bg-cm-purple`, `text-cm-muted`), so they won't clash with your existing Tailwind theme.
- Animations (`animate-cm-glow`, `animate-cm-fade`, etc.) are also defined in the config — no separate CSS file needed for keyframes.
- The carousel's smooth infinite scroll relies on JS `scrollBy` in `MovieRow`, so it works even if Tailwind's JIT purges unused arbitrary classes elsewhere in your project.
- Swap `data/movies.js` for real API data — every component expects the same `{ title, genre, rating, grad, tag }` shape.
