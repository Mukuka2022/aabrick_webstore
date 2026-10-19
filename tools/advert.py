"""The homepage's picture, rendered rather than screenshotted.

Two renders of the same living room at the photograph's own 1448 pixels,
cut down the middle and joined. Nothing is scaled up anywhere: the final
file is 1300 across, which is a reduction, so it stays sharp on a phone's
screen as well as a desk's.
"""

import os

from PIL import Image

D = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/closeup/")
OUT = ("/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"
       "/public/images/visualiser-shot.jpg")
WIDE = 1300

a = Image.open(D + "living-light.jpg").convert("RGB")
b = Image.open(D + "living-dark.jpg").convert("RGB")
w, h = a.size
assert b.size == (w, h)

# a little off the top: the picture is for a strip on a page, and the
# ceiling is not what is being sold
top = int(h * 0.10)
a = a.crop((0, top, w, h))
b = b.crop((0, top, w, h))
h = a.size[1]

half = w // 2
out = Image.new("RGB", (w, h))
out.paste(a.crop((0, 0, half, h)), (0, 0))
out.paste(b.crop((half, 0, w, h)), (half, 0))
for y in range(h):
    for dx in (-1, 0, 1):
        x = half + dx
        if 0 <= x < w:
            out.putpixel((x, y), (255, 255, 255))

out = out.resize((WIDE, int(round(WIDE * h / float(w)))), Image.LANCZOS)
out.save(OUT, "JPEG", quality=84, optimize=True, progressive=True)
print("wrote %d x %d, %.0f KB" % (out.width, out.height,
                                  os.path.getsize(OUT) / 1024.0))
