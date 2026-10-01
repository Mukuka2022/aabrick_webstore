"""Clean floor textures for the visualiser, cut out of the catalogue shots.

Marcopolo prints its name and the tile code across the top of most catalogue
photographs in orange. That is fine on a product card, where it reads as a
label, and impossible on a floor, where it repeats every 600mm.

Rather than paint the lettering out, which would mean inventing surface that
the customer is buying on, this takes the largest piece of each photograph
that does not contain it. A tile photograph is a picture of a repeating
material, so a clean piece of it is as true as the whole: nothing is added,
only less is shown.

The crop keeps the picture's own proportions. A 600x1200 tile stays twice as
long as it is wide, because the visualiser lays tiles at their real shape and
a square texture on an oblong tile would stretch the grain.

What it cannot do is change the scale. A texture cut to three quarters of the
photograph still fills a whole tile on the floor, so its grain is drawn about
a third larger than life. On stone, grain and plain colour that is invisible.
On a strong directional pattern it is not, which is why anything cropped
hard is left out rather than used.

    bench --site SITE execute aabrick_webstore.textures.run
    bench --site SITE execute aabrick_webstore.textures.check

Safe to run twice: it skips anything already made, and never writes over an
original. Delete the folder to start again.
"""

import os
import re

import frappe

SIZE = re.compile(r"\((\d+)\s*[xX]\s*(\d+)\)")

FOLDER = "tex"
MAX_PX = 900          # a floor texture never needs more, and the page loads many
THUMB_PX = 150        # the swatch in the picker, which is 78px at its biggest
QUALITY = 82

# Below this the texture is too small to hold up stretched across a room.
#
# Measured on the long edge, not the short one. The short side was the obvious
# test and the wrong one: a tile is photographed in its own shape, so a 600x1200
# comes in as a strip about 860 by 430, and taking the lettering off left a
# short side of 310 to 384 against a floor of 420. It threw out 48 of the 59
# oblong tiles for being oblong, while a 600x600 of exactly the same quality
# sailed through on a 590px square.
#
# And measured against the tile rather than as a flat number. What matters is
# pixels per millimetre of real tile: 600px holds a 1200mm tile at half a pixel
# per millimetre, and asking the same 600 of a 600mm tile is twice as strict as
# it needs to be. The flat floor was quietly dropping 600mm tiles whose crops
# came out at 568px, which is nearly a pixel per millimetre and perfectly good.
PX_PER_MM = 0.5
FLOOR_PX = 400        # however small the tile, below this it will not hold up
MIN_LONG_PX = 600     # the fallback, when the tile's real size is not known
# And below this fraction of the original, the grain is drawn far enough from
# life that the tile stops being an honest picture of itself.
MIN_KEEP = 0.62


# When the lettering is printed over a tile its own colour, a warm wood or a
# terracotta, _is_mark cannot tell the two apart and reports most of the
# picture as lettering. That is not a reading, it is a failure, and treating it
# as a reading threw away 25 perfectly good tiles. Past this much of the image
# the result is discarded and the band the lettering always occupies is taken
# off the top instead.
MARK_RUNAWAY = 0.55
MARK_BAND = 0.26


def _is_mark(r, g, b):
    """Marcopolo's print: the orange lettering, and the dark red logo.

    Two tests, because they are two different reds and one threshold cannot
    hold both. The lettering is a bright orange around 230,120,30. The logo
    stamped in a corner is far darker, around 143,47,51, which sat under the
    old r > 150 and sailed through: it was still sitting in the corner of the
    wall tile textures when Mukuka spotted it.

    The dark test is kept off the terracottas and the wood grains by their
    green channel. The logo has g around 47 and a warm wood has it around
    118, which separates them cleanly where the red channel alone does not.
    """
    if r > 150 and (r - b) > 85 and (r - g) > 30 and g < 200:
        return True
    return r > 110 and g < 95 and (r - g) > 60 and (r - b) > 55


def _still_printed(im, probe=180):
    """Marcopolo print left in a finished texture.

    The cutter is told where the print is and takes the largest clean piece,
    and that is a plan rather than a guarantee: a second stamp in another
    corner, or a crop that had to choose between two, can leave one behind.
    Rather than add a case each time one is found, the result is looked at.

    A tight patch is print. A wide one is the tile: a terracotta or an orange
    wood reads as ink everywhere, and the bounding box is what separates them.
    """
    w, h = im.size
    s = im.resize((probe, max(1, int(probe * h / float(w)))))
    px = s.load()
    sw, sh = s.size
    xs, ys, n = [], [], 0
    for y in range(sh):
        for x in range(sw):
            if _is_mark(*px[x, y]):
                n += 1
                xs.append(x)
                ys.append(y)
    if not n:
        return False
    frac = n / float(sw * sh)
    area = ((max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)) / float(sw * sh)
    return frac > 0.004 and area < 0.45


def _is_card(im, probe=200):
    """A product card rather than a photograph of a tile.

    Some of what the catalogue carries is not a tile at all: 25400 is a white
    sheet reading Type: Gloss wall tiles, Size: 250*400, with the logo in the
    corner. Laid on a floor that is a room with writing across it, and no
    cropping rescues it because there is no tile in the picture to crop to.

    Nearly all white with a little hard dark text in it is the signature. A
    pale tile is pale throughout and has grain; a card has paper and ink.
    """
    w, h = im.size
    s = im.resize((probe, max(1, int(probe * h / float(w)))))
    px = s.load()
    sw, sh = s.size
    pale = dark = 0
    for y in range(sh):
        for x in range(sw):
            r, g, b = px[x, y]
            if r > 232 and g > 232 and b > 232:
                pale += 1
            elif max(r, g, b) < 120:
                dark += 1
    n = float(sw * sh)
    return (pale / n) > 0.85 and (dark / n) > 0.003


def _mark_box(im, probe=320):
    """Where the lettering is, as fractions of the picture, or None.

    Only the top and bottom fifths are looked at. That is where it is printed,
    and a tile with a genuinely orange band through its middle is a tile, not
    a label.
    """
    w, h = im.size
    s = im.resize((probe, max(1, int(probe * h / float(w)))))
    sw, sh = s.size
    px = s.load()
    band = max(2, int(sh * 0.22))

    xs, ys = [], []
    for y in list(range(0, band)) + list(range(sh - band, sh)):
        for x in range(sw):
            r, g, b = px[x, y]
            if _is_mark(r, g, b):
                xs.append(x)
                ys.append(y)

    # A handful of stray pixels is noise in the photograph, not lettering.
    if len(xs) < max(30, int(sw * sh * 0.0012)):
        return None

    box = (min(xs) / float(sw), min(ys) / float(sh),
           (max(xs) + 1) / float(sw), (max(ys) + 1) / float(sh))
    if (box[2] - box[0]) * (box[3] - box[1]) > MARK_RUNAWAY:
        # The tile is the same colour as the print. Fall back to the band.
        return (0.0, 0.0, 1.0, MARK_BAND)
    return box


def _crop_box(w, h, mark):
    """The largest rectangle of the same proportions that misses the mark.

    Four places it could go, above the lettering, below it, or to either side.
    The biggest wins; the others are usually much smaller, because the name is
    printed across most of the width.
    """
    if not mark:
        return (0, 0, w, h), 1.0
    l, t, r, b = mark
    pad = 0.012
    bands = [
        (0, 0, 1.0, max(0.0, t - pad)),          # above
        (0, min(1.0, b + pad), 1.0, 1.0),        # below
        (0, 0, max(0.0, l - pad), 1.0),          # left
        (min(1.0, r + pad), 0, 1.0, 1.0),        # right
    ]
    best = None
    for bl, bt, br, bb in bands:
        bw, bh = (br - bl) * w, (bb - bt) * h
        if bw <= 1 or bh <= 1:
            continue
        # largest w:h rectangle inside this band
        scale = min(bw / float(w), bh / float(h))
        if best is None or scale > best[0]:
            cw, ch = w * scale, h * scale
            cx = bl * w + (bw - cw) / 2.0
            cy = bt * h + (bh - ch) / 2.0
            best = (scale, (int(cx), int(cy), int(cx + cw), int(cy + ch)))
    if not best:
        return None, 0.0
    return best[1], best[0]


def _out_dir():
    d = frappe.get_site_path("public", "files", FOLDER)
    os.makedirs(d, exist_ok=True)
    return d


def _candidates():
    """Published items whose group names a tile size, and that have a picture."""
    rows = frappe.db.sql(
        """
        SELECT item_code, website_image, item_group
        FROM `tabWebsite Item`
        WHERE published = 1 AND IFNULL(website_image, '') <> ''
        """,
        as_dict=True,
    )
    out = []
    for r in rows:
        m = SIZE.search(r.item_group or "")
        if not m:
            continue
        src = frappe.get_site_path("public", (r.website_image or "").lstrip("/"))
        if os.path.exists(src):
            out.append((r.item_code, src, int(m.group(1)), int(m.group(2))))
    return out


def _safe(code):
    return re.sub(r"[^A-Za-z0-9._-]", "_", code)


def build(code, src, redo=False, long_mm=None):
    """Make one texture. Returns (status, note).

    long_mm is the tile's own long edge in millimetres, which sets how many
    pixels the texture has to keep. Without it the flat MIN_LONG_PX is used.
    """
    from PIL import Image

    dst = os.path.join(_out_dir(), "%s.jpg" % _safe(code))
    if os.path.exists(dst) and not redo:
        return "kept", ""

    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        if _is_card(im):
            return "skipped", "a product card, not a photograph of the tile"
        mark = _mark_box(im)
        box, scale = _crop_box(w, h, mark)
        if box is None:
            return "skipped", "nothing left after the lettering"
        if mark and scale < MIN_KEEP:
            return "skipped", "only %d%% of the picture is clear" % (scale * 100)

        cut = im.crop(box)
        cw, ch = cut.size
        need = MIN_LONG_PX
        if long_mm:
            need = max(FLOOR_PX, int(PX_PER_MM * long_mm))
        if max(cw, ch) < need:
            return "skipped", ("clear piece is %dpx on its long edge, needs %d"
                               % (max(cw, ch), need))
        if _still_printed(cut):
            return "skipped", "print left in it after the cut"

        if max(cw, ch) > MAX_PX:
            k = MAX_PX / float(max(cw, ch))
            cut = cut.resize((max(1, int(cw * k)), max(1, int(ch * k))),
                             Image.LANCZOS)
        cut.save(dst, "JPEG", quality=QUALITY, optimize=True,
                 progressive=True)

        # A swatch as well. The picker now offers the whole range rather than
        # a couple of dozen, and a panel that fetched the full texture for
        # every one of them would pull several megabytes to draw a column of
        # 78px squares.
        tw, th = cut.size
        k = THUMB_PX / float(max(tw, th))
        if k < 1:
            thumb = cut.resize((max(1, int(tw * k)), max(1, int(th * k))),
                               Image.LANCZOS)
        else:
            thumb = cut
        thumb.save(os.path.join(_out_dir(), "%s-sm.jpg" % _safe(code)),
                   "JPEG", quality=78, optimize=True)

    return ("cropped" if mark else "copied"), "%dx%d" % cut.size


def run(redo=False):
    cands = _candidates()
    print("  %d published tiles with a picture" % len(cands))
    tally = {}
    skipped = []
    for code, src, w, h in cands:
        try:
            status, note = build(code, src, redo=redo, long_mm=max(w, h))
        except Exception as e:
            status, note = "failed", str(e)[:60]
        tally[status] = tally.get(status, 0) + 1
        if status in ("skipped", "failed"):
            skipped.append((code, note))

    for k in ("cropped", "copied", "kept", "skipped", "failed"):
        if tally.get(k):
            print("  %-8s %d" % (k, tally[k]))
    if skipped:
        print("  left out:")
        for code, note in skipped[:12]:
            print("    %-12s %s" % (code, note))
        if len(skipped) > 12:
            print("    and %d more" % (len(skipped) - 12))
    print("  textures are at /files/%s/" % FOLDER)


def texture_url(code):
    """The cleaned texture for a tile, or None if there is not one."""
    name = "%s.jpg" % _safe(code)
    if os.path.exists(os.path.join(frappe.get_site_path(
            "public", "files", FOLDER), name)):
        return "/files/%s/%s" % (FOLDER, name)
    return None


def thumb_url(code):
    """The swatch for the picker. Falls back to the texture itself, so a set
    built before thumbnails existed still shows something."""
    name = "%s-sm.jpg" % _safe(code)
    if os.path.exists(os.path.join(frappe.get_site_path(
            "public", "files", FOLDER), name)):
        return "/files/%s/%s" % (FOLDER, name)
    return texture_url(code)


def forget(code):
    """Drop a tile's texture and its swatch."""
    d = _out_dir()
    gone = 0
    for name in ("%s.jpg" % _safe(code), "%s-sm.jpg" % _safe(code)):
        path = os.path.join(d, name)
        if os.path.exists(path):
            os.remove(path)
            gone += 1
    return gone


def on_website_item(doc, method=None):
    """Re-cut one tile when somebody changes its photograph.

    Uploading a better picture and having to ask a developer to run a command
    before anybody can see it is the thing this site keeps trying not to be.
    Save the product and the visualiser has it.

    Three rules it has to obey.

    It never stops a save. A texture is a nicety and a product record is not,
    so everything here is inside a try and the worst case is that the texture
    is stale until the next run.

    It only works when the photograph actually changed. on_update fires for a
    price edit as readily as for a new picture, and re-cutting the catalogue
    one tile at a time on every save would be a slow way to achieve nothing.

    And it says when it refuses. A photograph rejected in silence looks like a
    photograph accepted, and whoever uploaded it would have no way of knowing
    the tile is still missing from the picker.
    """
    try:
        if not SIZE.search(doc.get("item_group") or ""):
            return

        image = (doc.get("website_image") or "").strip()
        if not image:
            if forget(doc.get("item_code")):
                frappe.msgprint(
                    "The tile texture has been removed with the photograph.",
                    indicator="orange", alert=True)
            return

        # A price edit is not a new picture. Already having a texture is the
        # second half of that: a tile cut before this hook existed should not
        # be re-cut on the next unrelated save either.
        if not doc.has_value_changed("website_image") \
                and texture_url(doc.get("item_code")):
            return

        src = frappe.get_site_path("public", image.lstrip("/"))
        if not os.path.exists(src):
            return

        m = SIZE.search(doc.get("item_group") or "")
        status, note = build(doc.get("item_code"), src, redo=True,
                             long_mm=max(int(m.group(1)), int(m.group(2))))

        if status in ("cropped", "copied"):
            frappe.msgprint(
                "Tile texture updated. It is in the visualiser now.",
                indicator="green", alert=True)
        else:
            # Leave nothing behind that the new picture has outdated.
            forget(doc.get("item_code"))
            frappe.msgprint(
                "This picture cannot be used in the tile visualiser: %s. "
                "The tile is still on the shop pages." % note,
                indicator="orange")
    except Exception:
        frappe.log_error(
            title="Tile texture for %s" % doc.get("item_code"),
            message=frappe.get_traceback())


def check():
    d = _out_dir()
    made = [f for f in os.listdir(d)
            if f.endswith(".jpg") and not f.endswith("-sm.jpg")]
    print("  %d textures built, out of %d published tiles with a picture"
          % (len(made), len(_candidates())))
    if made:
        total = sum(os.path.getsize(os.path.join(d, f)) for f in made)
        print("  %.1f KB in total, %.1f KB each on average"
              % (total / 1024.0, total / 1024.0 / len(made)))
