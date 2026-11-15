#!/usr/bin/env python3
"""
build.py — turns the photos you drop into originals/ into a fast, web-ready
portfolio: resized WebP variants, tiny blurred placeholders, video posters,
and data/manifest.js (which the site reads).

    python3 tools/build.py            # process everything new/changed
    python3 tools/build.py --force    # redo everything
    python3 tools/build.py --quality 80 --widths 640,1280,2000

Needs Python 3.8+ and Pillow:   pip install pillow
Video posters need ffmpeg on your PATH (optional; videos still work without).

Folder rules (see README.md):
    originals/_home/          frames for the rapidly-cycling home gallery
    originals/_archive/       loose images/videos for the Archive page (no series)
    originals/<series>/       one folder per project/series, images + videos
    originals/<series>/series.json   optional: title, year, description, cover, order
"""
import argparse, json, hashlib, os, re, shutil, subprocess, sys, base64, io
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageFilter
except ImportError:
    sys.exit("Pillow is required:  pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / "originals"
MEDIA = ROOT / "media"
MANIFEST = ROOT / "data" / "manifest.js"
CACHE = MEDIA / ".build-cache.json"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".gif"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v"}
WIDTHS = [640, 1280, 2000]
MAX_WIDTH = 2000           # the largest variant; also used by the lightbox
QUALITY = 82
LQIP_WIDTH = 24

try:  # HEIC straight from an iPhone, if the optional plugin is installed
    import pillow_heif  # noqa
    pillow_heif.register_heif_opener()
    IMAGE_EXT |= {".heic", ".heif"}
except ImportError:
    pass


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "untitled"


def titleize(slug):
    return re.sub(r"[-_]+", " ", slug).strip().title()


def natural_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def file_sig(p):
    st = p.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def load_cache():
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass
    return {}


def lqip(img):
    """A ~24px wide, blurred WebP as a data URI. Shown while the real image loads."""
    small = img.copy()
    small.thumbnail((LQIP_WIDTH, LQIP_WIDTH * 4))
    small = small.filter(ImageFilter.GaussianBlur(1))
    buf = io.BytesIO()
    small.save(buf, "WEBP", quality=40)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def process_image(src, out_dir, stem, widths, quality, force, cache):
    key = str(src.relative_to(ROOT))
    sig = file_sig(src)
    entry = cache.get(key)
    if entry and entry.get("sig") == sig and not force and all((out_dir / Path(s).name).exists() for s in entry["srcset"].values()):
        return entry["item"]

    img = Image.open(src)
    img = ImageOps.exif_transpose(img)        # honour camera rotation
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    if img.mode == "RGBA":                    # flatten transparency on white
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    w, h = img.size
    srcset = {}
    for tw in sorted(set(widths)):
        if tw > w and srcset:                 # never upscale; keep at least one size
            break
        tw = min(tw, w)
        th = round(h * tw / w)
        name = f"{stem}-{tw}.webp"
        out = out_dir / name
        if force or not out.exists():
            resized = img.resize((tw, th), Image.LANCZOS)
            resized.save(out, "WEBP", quality=quality, method=6)
        srcset[str(tw)] = f"media/{out_dir.name}/{name}"
    largest = max(srcset, key=int)
    item = {
        "type": "image",
        "name": stem,
        "src": srcset[largest],
        "srcset": srcset,
        "width": w, "height": h,
        "alt": titleize(stem),
        "lqip": lqip(img),
    }
    cache[key] = {"sig": sig, "srcset": srcset, "item": item}
    print(f"  image  {src.name}  ->  {', '.join(srcset)}px")
    return item


def process_video(src, out_dir, stem, force, cache):
    key = str(src.relative_to(ROOT))
    sig = file_sig(src)
    out = out_dir / (stem + src.suffix.lower())
    poster = out_dir / f"{stem}-poster.webp"
    entry = cache.get(key)
    if entry and entry.get("sig") == sig and not force and out.exists():
        return entry["item"]
    if force or not out.exists() or file_sig(out) != sig:
        shutil.copy2(src, out)
    item = {"type": "video", "name": stem, "src": f"media/{out_dir.name}/{out.name}", "alt": titleize(stem)}
    ff = shutil.which("ffmpeg") and shutil.which("ffprobe")
    if ff:
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=width,height", "-of", "csv=p=0", str(src)],
                capture_output=True, text=True, check=True).stdout.strip().split(",")
            item["width"], item["height"] = int(probe[0]), int(probe[1])
            if force or not poster.exists():
                tmp = out_dir / f"{stem}-poster.png"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", str(src),
                                "-frames:v", "1", str(tmp)], check=True)
                pimg = Image.open(tmp).convert("RGB")
                pimg.thumbnail((MAX_WIDTH, MAX_WIDTH))
                pimg.save(poster, "WEBP", quality=QUALITY)
                item["lqip"] = lqip(pimg)
                tmp.unlink()
            item["poster"] = f"media/{out_dir.name}/{poster.name}"
        except Exception as e:  # poster is a nicety; keep going
            print(f"  (no poster for {src.name}: {e})")
    cache[key] = {"sig": sig, "item": item}
    print(f"  video  {src.name}")
    return item


def read_series_json(folder):
    f = folder / "series.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text())
    except Exception as e:
        print(f"  ! could not read {f}: {e}")
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-encode everything")
    ap.add_argument("--quality", type=int, default=QUALITY)
    ap.add_argument("--widths", default=",".join(map(str, WIDTHS)))
    args = ap.parse_args()
    widths = [int(x) for x in args.widths.split(",") if x.strip()]

    if not ORIG.exists():
        sys.exit(f"No originals/ folder at {ORIG}. Create it and add a folder per series.")
    MEDIA.mkdir(exist_ok=True)
    (ROOT / "data").mkdir(exist_ok=True)
    cache = load_cache()

    folders = sorted([p for p in ORIG.iterdir() if p.is_dir() and not p.name.startswith(".")], key=natural_key)
    series_list, home_items, archive_items = [], [], []
    live_outputs = set()

    for folder in folders:
        meta = read_series_json(folder)
        slug = slugify(folder.name)
        out_dir = MEDIA / slug
        out_dir.mkdir(exist_ok=True)
        print(f"{folder.name}/")
        files = sorted([p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")], key=natural_key)
        order = meta.get("order") or []
        if order:  # explicit order first, then the rest alphabetically
            by_name = {p.name: p for p in files}
            files = [by_name[n] for n in order if n in by_name] + [p for p in files if p.name not in order]
        items = []
        for f in files:
            ext = f.suffix.lower()
            stem = slugify(f.stem)
            if ext in IMAGE_EXT:
                items.append(process_image(f, out_dir, stem, widths, args.quality, args.force, cache))
            elif ext in VIDEO_EXT:
                items.append(process_video(f, out_dir, stem, args.force, cache))
        for it in items:
            if "srcset" in it:
                live_outputs.update(it["srcset"].values())
            for k in ("src", "poster"):
                if it.get(k):
                    live_outputs.add(it[k])

        if folder.name.lower() in ("_home", "home"):
            home_items = [it for it in items if it["type"] == "image"]
            continue
        if folder.name.lower() in ("_archive", "archive"):
            archive_items = items
            continue
        if not items:
            print("  (empty, skipped)")
            continue
        cover = None
        if meta.get("cover"):
            cover = next((it for it in items if it["name"] == slugify(Path(meta["cover"]).stem)), None)
        if cover is None:
            cover = next((it for it in items if it["type"] == "image"), items[0])
        series_list.append({
            "slug": slug,
            "title": meta.get("title") or titleize(folder.name),
            "year": meta.get("year", ""),
            "description": meta.get("description", ""),
            "hidden": bool(meta.get("hidden", False)),
            "cover": cover,
            "items": items,
        })

    if not home_items:  # no _home folder: cycle through every series' images
        for s in series_list:
            home_items += [it for it in s["items"] if it["type"] == "image"][:6]

    # tag each home frame with the series it belongs to, so clicking it opens that series
    by_src = {it["src"]: s["slug"] for s in series_list for it in s["items"]}
    for it in home_items:
        it = dict(it)
    home = []
    for it in home_items:
        h = dict(it)
        h["series"] = by_src.get(it["src"]) or _guess_series(it, series_list)
        home.append(h)

    # remove outputs for originals that were deleted
    for p in MEDIA.rglob("*"):
        if p.is_file() and p.name != CACHE.name:
            rel = str(p.relative_to(ROOT)).replace(os.sep, "/")
            if rel not in live_outputs:
                p.unlink()
                print(f"  removed stale {rel}")
    for d in MEDIA.iterdir():
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    for k in list(cache):
        if not (ROOT / k).exists():
            del cache[k]

    if not archive_items:  # no _archive folder: the archive shows everything from every project
        archive_items = [it for s in series_list for it in s["items"]]
    manifest = {"generated": True, "home": home, "series": series_list, "archive": archive_items}
    MANIFEST.write_text(
        "// Generated by tools/build.py — do not edit by hand; edit originals/ and re-run.\n"
        "window.PORTFOLIO = " + json.dumps(manifest, indent=1) + ";\n")
    CACHE.write_text(json.dumps(cache))
    print(f"\nWrote {MANIFEST.relative_to(ROOT)}: {len(home)} home frames, {len(series_list)} projects, {len(archive_items)} archive items.")


def _guess_series(item, series_list):
    """Home frame named like a series folder ('coastline-03.jpg') links to that series."""
    for s in series_list:
        if item["name"].startswith(s["slug"]):
            return s["slug"]
    return None


if __name__ == "__main__":
    main()
