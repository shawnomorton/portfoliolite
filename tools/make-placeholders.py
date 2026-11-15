#!/usr/bin/env python3
"""Generates abstract placeholder 'photographs' so the site has something to show.
Delete originals/* and drop in your own work when ready. Run from the site folder."""
import random, math, json, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / "originals"
random.seed(7)

PALETTES = {
    "coastline": [((214, 226, 232), (120, 150, 160)), ((240, 236, 226), (90, 110, 120)), ((200, 210, 205), (60, 80, 90))],
    "night-drive": [((20, 18, 26), (120, 60, 40)), ((10, 12, 20), (200, 140, 60)), ((30, 20, 30), (80, 90, 140))],
    "lab-light": [((245, 243, 238), (150, 160, 170)), ((230, 232, 236), (40, 50, 70)), ((250, 248, 240), (190, 120, 90))],
}
SHAPES = [(3000, 2000), (2000, 3000), (2400, 3000), (3000, 1690), (2600, 2600)]


def grain(img, amount=12):
    import numpy as np  # optional
    arr = np.asarray(img).astype("int16")
    noise = np.random.randint(-amount, amount + 1, arr.shape[:2] + (1,))
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"))


def frame(w, h, c1, c2, kind):
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    # vertical gradient
    for y in range(h):
        t = y / h
        col = tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)
    if kind == 0:   # horizon
        hy = int(h * random.uniform(0.45, 0.7))
        d.rectangle([0, hy, w, h], fill=tuple(max(0, c - 40) for c in c2))
        sun = int(min(w, h) * random.uniform(0.05, 0.12))
        cx = int(w * random.uniform(0.2, 0.8))
        d.ellipse([cx - sun, hy - sun * 2, cx + sun, hy], fill=tuple(min(255, c + 70) for c in c1))
    elif kind == 1:  # light streaks
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, w); ww = random.randint(w // 60, w // 12)
            col = tuple(min(255, c + random.randint(30, 110)) for c in c2)
            d.polygon([(x, 0), (x + ww, 0), (x + ww + w // 8, h), (x + w // 8, h)], fill=col)
        img = img.filter(ImageFilter.GaussianBlur(w // 150))
    elif kind == 2:  # blocks / architecture
        for _ in range(random.randint(2, 5)):
            x0 = random.randint(0, w); y0 = random.randint(0, h)
            x1 = min(w, x0 + random.randint(w // 8, w // 2)); y1 = min(h, y0 + random.randint(h // 8, h // 2))
            col = tuple(max(0, min(255, c + random.randint(-60, 60))) for c in c2)
            d.rectangle([x0, y0, x1, y1], fill=col)
    else:            # soft circle / portrait-ish
        r = int(min(w, h) * random.uniform(0.2, 0.4))
        cx, cy = w // 2 + random.randint(-w // 8, w // 8), h // 2 + random.randint(-h // 8, h // 8)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(min(255, c + 40) for c in c1))
        img = img.filter(ImageFilter.GaussianBlur(w // 80))
    try:
        img = grain(img)
    except Exception:
        pass
    return img


series_meta = {
    "coastline": {"title": "Coastline", "year": "2025", "description": "Fog, tide lines and long exposures along the Pacific edge."},
    "night-drive": {"title": "Night Drive", "year": "2024", "description": "Sodium light, wet asphalt and the hour after the city goes quiet."},
    "lab-light": {"title": "Lab Light", "year": "2026", "description": "Still lifes from the bench: glass, gradients and the glow of a cytometer at 2 a.m."},
}
home = ORIG / "_home"; home.mkdir(parents=True, exist_ok=True)
for slug, meta in series_meta.items():
    d = ORIG / slug; d.mkdir(parents=True, exist_ok=True)
    (d / "series.json").write_text(json.dumps(meta, indent=2) + "\n")
    for i in range(1, 7):
        w, h = random.choice(SHAPES)
        c1, c2 = random.choice(PALETTES[slug])
        img = frame(w, h, c1, c2, random.randint(0, 3))
        img.save(d / f"{slug}-{i:02d}.jpg", quality=92)
        if i <= 3:
            img.save(home / f"{slug}-{i:02d}.jpg", quality=92)
    print("made", slug)

# a loose archive: mixed shapes and palettes
arch = ORIG / "_archive"; arch.mkdir(parents=True, exist_ok=True)
for i in range(1, 13):
    slug = random.choice(list(PALETTES))
    w, h = random.choice(SHAPES)
    c1, c2 = random.choice(PALETTES[slug])
    frame(w, h, c1, c2, random.randint(0, 3)).save(arch / f"archive-{i:02d}.jpg", quality=88)
print("made _archive")

# a short placeholder video, if ffmpeg is around
if shutil.which("ffmpeg"):
    out = ORIG / "night-drive" / "night-drive-07.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "color=c=0x14121a:s=1280x720:d=6,geq=r='r(X,Y)+90*sin(X/120+T*2)*sin(Y/90)':g='g(X,Y)+40*sin(X/120+T*2)':b='b(X,Y)+30*sin(Y/90+T)'",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    print("made video", out.name)
