# MS2 Mini‑QBank (GH Pages + PWA)

This folder is ready to drop into a GitHub repository and serve from **GitHub Pages**.

## Files
- `index.html` — the single‑page app (practice + exam modes, keyboard shortcuts, local persistence).
- `manifest.json` — PWA manifest (name, icons, theme).
- `sw.js` — service worker for offline caching.
- `icon-192.png`, `icon-512.png` — app icons.
  
## Host on GitHub Pages
1. Create a new public repo (or use an existing one).
2. Add these files to the root of the repo.
3. Commit & push.
4. In the repo: **Settings → Pages → Build and deployment → Source: Deploy from a branch**.  
   Select your default branch and **root** (`/`) folder, then **Save**.
5. Wait for the green “Your site is published” banner. The app will be live at the URL displayed.

> Tip: The app is installable (Add to Home Screen). Offline support is provided by `sw.js`.

## Privacy
All progress data is stored **locally** in your browser (`localStorage`). Nothing is sent to a server.

— Built 2025-10-11
