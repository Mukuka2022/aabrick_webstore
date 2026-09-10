"""The "homes built with AABrick" gallery.

Four photographs of finished rooms. They live in the app rather than the site
file store so they travel with a git deploy, exactly like the hero.

The section renders only when all four slots are filled. A gallery of one or
two reads as something half broken rather than as a smaller gallery, and an
empty one on a live homepage is worse than no section at all.

Usage, from the bench directory:

    bench --site www.aabrick.com execute \\
        aabrick_webstore.showcase.set_slot \\
        --kwargs "{'slot': 1, 'path': '/files/kitwe-sitting-room.jpg',
                   'caption': 'Sitting room, Kitwe', 'detail': 'Tile 86072'}"

    bench --site www.aabrick.com execute aabrick_webstore.showcase.status
    bench --site www.aabrick.com execute \\
        aabrick_webstore.showcase.clear_slot --args "[2]"

Paths may be anywhere on the server, or a /files/... URL as it appears after
uploading through the ERPNext file manager.
"""

import json
import os

import frappe

HERE = os.path.dirname(__file__)
IMAGES = os.path.join(HERE, "public", "images")
CAPTIONS = os.path.join(HERE, "showcase.json")

SLOTS = (1, 2, 3, 4)
SIZE = (900, 990)          # 10:11, the same shape as the category cards
MIN_WIDTH = 900            # rendered up to ~350px wide, so 900 is a 2x source


def _name(slot):
    return "showcase-%d.jpg" % slot


def _path(slot):
    return os.path.join(IMAGES, _name(slot))


def _captions():
    if not os.path.exists(CAPTIONS):
        return {}
    try:
        with open(CAPTIONS, encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        return {}


def _write_captions(data):
    with open(CAPTIONS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _resolve(path):
    if path.startswith("/files/"):
        return frappe.get_site_path("public", path.lstrip("/"))
    if path.startswith("/private/files/"):
        return frappe.get_site_path(path.lstrip("/"))
    return os.path.expanduser(path)


def _crop(im, size):
    """Fill and crop, biased above centre so ceilings and walls survive rather
    than floor."""
    from PIL import Image

    w, h = size
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (im.width - w) // 2
    top = int((im.height - h) * 0.35)
    return im.crop((left, top, left + w, top + h))


def set_slot(slot=None, path=None, caption="", detail=""):
    from PIL import Image

    slot = int(slot or 0)
    if slot not in SLOTS:
        frappe.throw("slot must be 1, 2, 3 or 4")

    src = _resolve(path or "")
    if not os.path.exists(src):
        print("No file at %s" % src)
        return

    im = Image.open(src)
    print("source: %s  %sx%s" % (os.path.basename(src), im.width, im.height))

    if im.width < MIN_WIDTH:
        print(
            "\nREFUSED: %spx wide. These render about 350px across, so a %spx\n"
            "source is the minimum that still looks sharp on a good screen."
            % (im.width, MIN_WIDTH)
        )
        return

    os.makedirs(IMAGES, exist_ok=True)
    out = _path(slot)
    _crop(im.convert("RGB"), SIZE).save(
        out, "JPEG", quality=82, optimize=True, progressive=True
    )
    print("  wrote %-16s %sx%-5s %6.0f KB" % (_name(slot), SIZE[0], SIZE[1], os.path.getsize(out) / 1024))

    data = _captions()
    data[str(slot)] = {"caption": caption or "", "detail": detail or ""}
    _write_captions(data)

    status()


def clear_slot(slot):
    slot = int(slot)
    if os.path.exists(_path(slot)):
        os.remove(_path(slot))
        print("removed %s" % _name(slot))
    data = _captions()
    data.pop(str(slot), None)
    _write_captions(data)
    status()


def status():
    data = _captions()
    filled = 0
    print("\nShowcase slots:")
    for slot in SLOTS:
        if os.path.exists(_path(slot)):
            filled += 1
            meta = data.get(str(slot), {})
            print("  %d  %-16s %s" % (slot, _name(slot), meta.get("caption") or "(no caption)"))
        else:
            print("  %d  empty" % slot)
    if filled == len(SLOTS):
        print("\nAll four filled: the section is live. Run bench build --app aabrick_webstore.")
    else:
        print("\n%d of 4 filled: the section stays hidden until all four are in." % filled)


def context():
    """Used by the homepage. Returns [] unless every slot is filled."""
    if not all(os.path.exists(_path(s)) for s in SLOTS):
        return []
    data = _captions()
    out = []
    for slot in SLOTS:
        meta = data.get(str(slot), {})
        out.append({
            "src": "/assets/aabrick_webstore/images/" + _name(slot),
            "caption": meta.get("caption") or "",
            "detail": meta.get("detail") or "",
        })
    return out
