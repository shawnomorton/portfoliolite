# Photo Portfolio

A fast, minimal photography portfolio in the spirit of brianchorski.com: a home page
that flickers rapidly through your frames, a **Projects** index of your organised
series (one page each, with images and video), and an **Archive** wall for everything
else. Static HTML/CSS/JS, no build tool, no framework. Host it
on GitHub Pages, Netlify, or any folder on a web server.

```
photo-portfolio/
├── index.html        home: cycling gallery + Projects index
├── series.html       one project (series.html?s=<folder-name>)
├── archive.html      the Archive wall
├── info.html         bio and contact
├── css/style.css
├── js/config.js      ← your name, email, speed, layout: edit this
├── js/app.js
├── data/manifest.js  ← generated, lists every photo (don't edit by hand)
├── originals/        ← YOUR PHOTOS GO HERE (full size, any common format)
│   ├── _home/        frames for the home-page flicker
│   ├── _archive/     loose photos for the Archive tab (no series)
│   ├── coastline/    one folder = one project
│   └── night-drive/
├── media/            ← generated: resized WebP versions the site actually serves
└── tools/build.py    ← run after you add or change photos
```

The folders that ship with it hold placeholder "photos". Delete everything in
`originals/` and add your own.

## Adding photos (the whole workflow)

1. **Make a folder per project** inside `originals/`. The folder name becomes the URL
   and the default title: `originals/desert-roads/` → "Desert Roads". Projects are what
   the **Projects** tab lists.
2. **Drop in images and videos.** JPG, PNG, TIFF, WebP, HEIC (see below), MP4, WebM, MOV.
   Files show in filename order, so name them `01.jpg, 02.jpg …` or anything that sorts
   the way you want.
3. **Put a few frames in `originals/_home/`** for the home page. Copies of your best
   shots work well; 8 to 20 is a good number. A frame named like its series
   (`desert-roads-04.jpg`) links to that series when double-clicked. If `_home/` is
   empty or missing, the home page cycles the first six images of every series.
4. **Throw anything else into `originals/_archive/`.** The **Archive** tab shows every
   image and video in that folder as a loose wall, in filename order (set
   `shuffleArchive: true` in the config for a random order each visit). If there is no
   `_archive/` folder, the Archive shows every image from every project instead.
5. **Run the build:**

   ```sh
   pip install pillow        # once
   python3 tools/build.py    # every time you add, remove or replace photos
   ```

   It only re-encodes files that changed, removes outputs for files you deleted, and
   rewrites `data/manifest.js`. Then open `index.html` (or push to your host).

### Optional `series.json`

Drop a `series.json` into a series folder to control its details:

```json
{
  "title": "Desert Roads",
  "year": "2025",
  "description": "Two weeks on US-50. Shot on Portra 400.",
  "cover": "07.jpg",
  "order": ["07.jpg", "02.jpg", "roadside.mp4"],
  "hidden": false
}
```

Everything is optional. `cover` picks the thumbnail on the index; `order` lists the files
that should come first (the rest follow alphabetically); `hidden: true` keeps a series
out of the index while you work on it (it is still reachable by URL).

### Videos

Any `.mp4`, `.webm` or `.mov` in a series folder shows inline with native controls,
muted-autoplay-free, and `playsinline` so iPhones don't go full screen. If `ffmpeg` is
installed, the build grabs a poster frame automatically. Keep videos web-sized: export
1080p H.264 MP4 at a moderate bitrate (8 to 12 Mbps is plenty) and under a minute or two.
For long or many videos, host on Vimeo/YouTube instead and link from the description.

Tip: `ffmpeg -i in.mov -vf scale=-2:1080 -c:v libx264 -crf 23 -preset slow -movflags +faststart -c:a aac out.mp4`

### HEIC from an iPhone

`pip install pillow-heif` and the build reads `.heic` directly.

## Image size and quality: what the build does and why it loads fast

- **Three widths per photo** (640, 1280, 2000 px) as WebP at quality 82. The browser
  picks the smallest one that fills the viewport (`srcset`/`sizes`), so a phone downloads
  about 60 KB per image instead of 5 MB.
- **2000 px is the ceiling** for the biggest size. On a 4K display it is still sharp; above
  that you pay in bytes for detail nobody can see. Change it with
  `python3 tools/build.py --widths 640,1280,2400 --force` if you want more.
- **Quality 82** is the sweet spot for WebP photographs; drop to `--quality 75` for
  grainy or very large sets, raise to 88 for clean studio work. Re-run with `--force`
  after changing it.
- **Blurred placeholders**: each photo gets a 24 px preview embedded in the manifest,
  so something appears instantly and the real image fades in over it.
- **Lazy loading**: images below the fold and on series pages load only as you scroll.
  Width and height are set on every `<img>`, so nothing jumps around while loading.
- **Home page**: the first two frames load with high priority and the rest stream in;
  the cycler skips frames that haven't arrived, so the rhythm never shows a blank.
- **Keep the originals out of the site**: upload the `media/` folder, not `originals/`.
  If you deploy with git, add `originals/` to `.gitignore` (it is there, commented).
  Your originals stay on your disk as the source of truth.

Export tips before you even run the build: export from Lightroom/Capture One at
2000 px on the long edge, sRGB, quality 90 JPG. That keeps `originals/` small too and
the build has nothing to downscale.

## Settings (`js/config.js`)

| Key | What it does |
| --- | --- |
| `name`, `tagline`, `email`, `instagram`, `location`, `bio` | Header, Contact link, Information page |
| `cycleMs` | Milliseconds per frame on the home page (420 by default; 250 is frantic, 800 is calm) |
| `shuffleHome` | Random order on every visit |
| `shuffleArchive` | Random order for the Archive wall |
| `pauseOnHover` | Hold the frame under the mouse (desktop only) |
| `openSeriesInNewTab` | `true` opens a project in a new browser tab |
| `singlePage` | `true` runs everything from `index.html` with `#` links (for hosts that serve one page) |
| `layout` | `"feed"` (one large image after another) or `"grid"` |

Home page controls: click or tap pauses and resumes, double-click opens the series the
frame belongs to, arrow keys step through frames, Space pauses. On a series page, click
an image for a full-screen viewer; arrow keys, swipe, or click to move on; Esc to close.

## Colours and type

Everything is in the `:root` block at the top of `css/style.css`. The page colour is the
warm off-white `#eeeee9`; change `--bg` there to change it everywhere (header, viewer,
all pages). The HTML files carry `data-theme="light"` so the site always uses that
colour; remove that attribute if you'd rather follow the visitor's dark-mode setting.

## Git and GitHub (the easy way)

This folder is already a git repository with one commit. Connect it to GitHub once:

```sh
# 1. On github.com create an EMPTY public repository (no README), e.g. "portfolio"
# 2. In this folder:
git remote add origin https://github.com/<your-username>/portfolio.git
git branch -M main
git push -u origin main
# 3. On GitHub: Settings > Pages > Source: main branch, root folder.
```

Your site is then at `https://<your-username>.github.io/portfolio/`.

**Every time you add photos:** put them in `originals/`, then run

```sh
tools/publish.sh "Add Iceland series"     # Mac / Linux
tools\publish.bat "Add Iceland series"    # Windows
```

It rebuilds the optimised images, commits, and pushes. `originals/` is git-ignored, so
your full-size files never leave your computer.

## Hosting

**GitHub Pages:** push this folder to a repository, then Settings › Pages › source
`main`, root folder. **Any static host:** upload everything except `originals/`.
**Locally:** double-click `index.html`, or `python3 -m http.server 8000` and open
http://localhost:8000.

## Placeholders

`tools/make-placeholders.py` generated the demo images. You will never need it again;
delete it along with the demo folders in `originals/` when you add your own work.
