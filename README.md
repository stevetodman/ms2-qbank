# Update Pack: favicon + Apple Touch + Versioning

**What this does**
- Adds `favicon.ico` and `apple-touch-icon.png` so installs and tabs look polished.
- Shows a **version pill** (e.g., `v1.0`) in the header.
- Bumps the service worker cache to **v3** so updates appear immediately after deploy.

**How to apply**
1. Drop these files into your repo root (replace existing ones):
   - `index.html`
   - `manifest.json`
   - `sw.js`
   - `icon-192.png`
   - `icon-512.png`
   - `apple-touch-icon.png`
   - `favicon.ico`
2. Commit & push.
3. Visit your site and do a hard refresh (Cmd–Shift–R).

**How to cut a new release later**
- Edit `index.html`: set `const VERSION = "v1.1";`
- Edit `sw.js`: bump `const CACHE = 'qbank-v4';`
- Commit & push.

That’s it.
