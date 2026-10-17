"""Take the pink off everything that is not going to be tiled.

The pink was only ever a tracing key, the way the blue was on the floors.
The floor disappears under a tile and so, now, does the wall; but the ceiling
is not a wall and nobody tiles one, so it stayed pink, and a few rims too
narrow for the span tracer to keep went with it. Against a tiled wall those
read as a fault rather than as a key, so any pink left over after the mask is
repainted as the warm off-white the room was asked for in the first place.

Brightness is kept exactly as it is. Only the colour is taken out, so every
shadow and every downlight on the ceiling survives.
"""
import io
import json
import os

from PIL import Image

SRC = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/images")
W = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls/walls.json")
APP = "/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"

ROOMS = [(19, "ensuite"), (20, "kitchen"), (18, "bathroom")]
HUE, SAT = 10.0, 0.72
FADE = 0.30        # below this the pink is only bounced light, and stays
# the warm off-white the rooms were asked for, as a tint
TINT = (1.000, 0.976, 0.953)


def hsv(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx / 255.0
    d = mx - mn
    if mx == 0 or d == 0:
        return 0.0, 0.0, v
    s = d / float(mx)
    if mx == r:
        h = 60.0 * (((g - b) / float(d)) % 6)
    elif mx == g:
        h = 60.0 * (((b - r) / float(d)) + 2)
    else:
        h = 60.0 * (((r - g) / float(d)) + 4)
    return h, s, v


walls = json.load(io.open(W, encoding="utf-8"))

for n, slug in ROOMS:
    im = Image.open("%s/%d.webp" % (SRC, n)).convert("RGB")
    w, h = im.size
    px = im.load()

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
    for y in range(h):
        row = y * w
        for x in range(w):
            if not keep[row + x]:
                continue
            for dy in (-2, -1, 0, 1, 2):
                yy = y + dy
                if yy < 0 or yy >= h:
                    continue
                r2 = yy * w
                for dx in (-2, -1, 0, 1, 2):
                    xx = x + dx
                    if 0 <= xx < w:
                        grown[r2 + xx] = 1

    ref, ref_sat = None, None
    from collections import Counter
    c = Counter()
    for y in range(int(h * 0.08), int(h * 0.32), 2):
        for x in range(0, w, 2):
            hh, ss, vv = hsv(*px[x, y])
            if ss > 0.40 and vv > 0.12:
                c[round(hh)] += 1
    ref = max(c, key=lambda k: sum(c.get(k + dd, 0) for dd in range(-4, 5)))
    sats = sorted(hsv(*px[x, y])[1]
                  for y in range(int(h * 0.08), int(h * 0.32), 2)
                  for x in range(0, w, 2)
                  if hsv(*px[x, y])[1] > 0.40 and hsv(*px[x, y])[2] > 0.12
                  and min(abs(hsv(*px[x, y])[0] - ref),
                          360 - abs(hsv(*px[x, y])[0] - ref)) < HUE)
    ref_sat = sats[len(sats) // 2]
    floor_sat = ref_sat * SAT

    fixed = 0
    for y in range(h):
        row = y * w
        for x in range(w):
            if grown[row + x]:
                continue
            r, g, b = px[x, y]
            hh, ss, vv = hsv(r, g, b)
            if ss < FADE or vv < 0.10:
                continue
            dd = abs(hh - ref)
            if dd > 180:
                dd = 360 - dd
            if dd >= HUE:
                continue
            # A ceiling is paler than the wall below it but the same pink,
            # so a single cut either leaves it or starts taking the warm
            # light off the porcelain. It is a ramp instead: full strength
            # at wall paint, nothing at all by the time the colour is only
            # the pink light bouncing around the room, and no seam where a
            # ceiling meets a wall.
            k = (ss - FADE) / (floor_sat - FADE)
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
    print("  %-10s %6d pixels repainted  (%.1f%% of the room)"
          % (slug, fixed, 100.0 * fixed / (w * h)))

print("leftover pink repainted")
