"""Take the paint off everything that is not going to be tiled.

The wall colour was only ever a tracing key, the way the blue was on the
floors. The floor disappears under a tile and so, now, does the wall; but
the ceiling is not a wall and nobody tiles one, and a few rims come out too
narrow for the span tracer to keep. Against a tiled wall those read as a
fault rather than as a key, so whatever is left over after the mask is
repainted as the warm off-white the room was asked for in the first place.

Brightness is kept exactly as it is. Only the colour is taken out, so every
shadow and every downlight on the ceiling survives.

Run this last: it needs the wall mask to know what to leave alone. It takes
the same hint per room as walltrace.py, and must be given the same one, or
it will measure one colour and the tracer will have masked another.
"""
import io
import json
import os

from PIL import Image

import keycolour

SRC = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/images")
W = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls/walls.json")
APP = "/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"

# Must match walltrace.py, room for room and hint for hint.
ROOMS = [
    (19, "ensuite",  10.0),
    (23, "kitchen",  85.0),
    (18, "bathroom", 10.0),
]

FADE = 0.30        # below this the colour is only bounced light, and stays
GROW = 2           # pixels the keep-mask is widened by
# the warm off-white the rooms were asked for, as a tint
TINT = (1.000, 0.976, 0.953)

walls = json.load(io.open(W, encoding="utf-8"))

for n, slug, hint in ROOMS:
    im = Image.open("%s/%d.webp" % (SRC, n)).convert("RGB")
    w, h = im.size
    px = im.load()

    found = keycolour.paint(px, w, h, hint)
    if found is None:
        print("  %-10s no paint near %.0f degrees, left alone" % (slug, hint))
        continue
    ref, ref_sat, win = found

    d = walls[slug]
    step = d["step"]
    keep = bytearray(w * h)          # 1 where a tile will go anyway
    for col in d["cols"]:
        x0 = col[0]
        for i in range(1, len(col), 2):
            for y in range(col[i], min(col[i + 1] + 1, h)):
                row = y * w
                for x in range(x0, min(x0 + step, w)):
                    keep[row + x] = 1

    # the walls were sampled with a slight blur, so the mask stops a pixel
    # or two short of the true edge; grow it so a repaint cannot eat into
    # what the tile is about to cover
    grown = bytearray(keep)
    span = range(-GROW, GROW + 1)
    for y in range(h):
        row = y * w
        for x in range(w):
            if not keep[row + x]:
                continue
            for dy in span:
                yy = y + dy
                if yy < 0 or yy >= h:
                    continue
                r2 = yy * w
                for dx in span:
                    xx = x + dx
                    if 0 <= xx < w:
                        grown[r2 + xx] = 1

    full = ref_sat * keycolour.LO    # by here it is paint, not bounced light
    ceiling = ref_sat * keycolour.HI  # past here it is something else entirely

    fixed = 0
    for y in range(h):
        row = y * w
        for x in range(w):
            if grown[row + x]:
                continue
            r, g, b = px[x, y]
            hh, ss, vv = keycolour.hsv(r, g, b)
            if ss < FADE or ss > ceiling or vv < 0.10:
                continue
            if keycolour.apart(hh, ref) >= win:
                continue
            # A ceiling is paler than the wall below it but the same colour,
            # so a single cut either leaves it or starts taking the warm
            # light off the porcelain. It is a ramp instead: full strength
            # at wall paint, nothing at all by the time the colour is only
            # the light bouncing around the room, and no seam where a
            # ceiling meets a wall.
            k = (ss - FADE) / (full - FADE) if full > FADE else 1.0
            if k > 1.0:
                k = 1.0
            L = 0.299 * r + 0.587 * g + 0.114 * b
            px[x, y] = (
                min(255, int(r + (L * TINT[0] - r) * k)),
                min(255, int(g + (L * TINT[1] - g) * k)),
                min(255, int(b + (L * TINT[2] - b) * k)))
            fixed += 1

    dst = os.path.join(APP, "public/images/scene-%s.jpg" % slug)
    im.save(dst, "JPEG", quality=88, optimize=True, progressive=True)
    print("  %-10s hue %3.0f  sat %.2f  window %2.0f   %6d pixels repainted"
          "  (%.1f%% of the room)"
          % (slug, ref, ref_sat, win, fixed, 100.0 * fixed / (w * h)))

print("leftover paint repainted")
