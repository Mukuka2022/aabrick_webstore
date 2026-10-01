"""The tiles the visualiser can actually lay, and the rooms it lays them in.

Marcopolo prints its name and the tile code across the top of most of its
catalogue shots in orange. That is fine on a product card, where it reads as
a label, and impossible on a floor, where it repeats every 600mm. It used to
rule out all but a couple of dozen tiles, which were listed here by hand.

textures.py now cuts the largest clean piece out of each photograph instead,
so the list is a query again: a tile is offered if a texture was built for
it. See that module for what it will and will not cut.

SKIP is for the ones that come out wrong anyway. A crop moves the middle of
the picture, which does not matter on stone or plain colour and does matter
on a tile with a motif centred in it, and no test for that is as good as
somebody looking. Codes put here are left out of the picker.

Sizes come from the item group, which spells them out: (600X600), (800X800),
(300X300). That is what lets a tile lay at true scale rather than at whatever
size looks about right.
"""

import re

import frappe

from aabrick_webstore import textures
from aabrick_webstore.overrides.website_item import describe_group

SIZE = re.compile(r"\((\d+)\s*[xX]\s*(\d+)\)")

# The item group, pulled apart. "Glazed Porcelain Tiles (600X600) - 88XXX" and
# "Glazed Porcelain Tiles D (600X600) - 86XXX" are the same range in two
# grades, and the D can sit either side of the brackets.
#
# This reads the item group rather than describe_group's label, which spells
# the two grades differently: the A grade comes back "Matt Porcelain Tile
# 600x600" and the B grade "Matt Porcelain Tiles (600X600)", so grouping on
# the label would file the same range under two headings.
RANGE = re.compile(
    r"^(?P<finish>.+?)\s+Tiles?\s*(?P<d1>D)?\s*"
    r"\((?P<w>\d+)\s*[xX]\s*(?P<h>\d+)\)\s*(?P<d2>D)?\s*(?:-.*)?$")

# Tiles whose cut texture is wrong even though it is clean. See the note above.
SKIP = []

# B grade is sold but not shown here. A visualiser is for choosing how a floor
# will look, and the two grades of a range look the same: the difference is in
# the tile, not the picture, so showing both doubled the picker for nothing a
# customer could see. They are still on the shop pages, where the price and
# the grade are next to each other and the distinction means something.
#
# One line to let them back in. The swatch still knows how to mark a B grade,
# so nothing else has to change.
INCLUDE_B_GRADE = False

# This lays floors, so it offers floor tiles. Widening the picker from a hand
# written list to a query swept in 43 wall tiles, which is worse than it looks:
# a wall tile is not rated to be walked on, and a customer who picked one here
# because it looked right in a kitchen would be buying the wrong thing.
NOT_FLOOR = ("wall",)


def tiles():
    """The tiles there is a clean texture for, ready for the page to draw."""
    rows = frappe.db.sql(
        """
        SELECT w.item_code, w.web_item_name, w.route, w.item_group,
               ip.price_list_rate
        FROM `tabWebsite Item` w
        LEFT JOIN `tabItem Price` ip
          ON ip.item_code = w.item_code AND ip.price_list = 'Web Price List'
        WHERE w.published = 1 AND IFNULL(w.website_image, '') <> ''
        GROUP BY w.item_code
        """,
        as_dict=True,
    )

    skip = set(SKIP)
    out = []
    for r in rows:
        if r.item_code in skip:
            continue
        m = SIZE.search(r.item_group or "")
        if not m:
            continue
        image = textures.texture_url(r.item_code)
        if not image:
            continue
        rng = RANGE.match((r.item_group or "").strip())
        label, _s, _f, grade = describe_group(r.item_group)
        if grade and not INCLUDE_B_GRADE:
            continue
        if any(w in label.lower() for w in NOT_FLOOR):
            continue
        out.append({
            "code": r.item_code,
            "name": r.web_item_name or r.item_code,
            "route": "/" + (r.route or ""),
            "group": label + (" (B Grade)" if grade else ""),
            # What the picker files it under, and the B marker on the swatch.
            "range": (rng.group("finish") if rng else label),
            "size": ("%s \u00d7 %s" % (m.group(1), m.group(2))),
            "grade": bool(grade),
            "image": image,
            "thumb": textures.thumb_url(r.item_code),
            "w": int(m.group(1)),
            "h": int(m.group(2)),
            "price": r.price_list_rate,
        })

    # Within a heading: A grade before B, then by code, so the picker reads
    # as the catalogue does rather than in whatever order the database
    # answered.
    out.sort(key=lambda t: (t["range"], t["w"], t["h"], t["grade"], t["code"]))
    return out


def groups():
    """The tiles in the headed sets the picker shows them in.

    Biggest range first. The picker is for browsing and the two 600x600
    porcelains are three quarters of what AABrick sells, so burying them under
    an alphabet would be tidy and useless.

    Only A grade reaches this, unless INCLUDE_B_GRADE is turned back on. If
    it is, both grades of a range share a heading rather than making two:
    they are the same tile, and the swatch carries the marker that says which.
    """
    out = []
    for t in tiles():
        key = (t["range"], t["w"], t["h"])
        for g in out:
            if g["key"] == key:
                g["entries"].append(t)
                break
        else:
            out.append({
                "key": key,
                "label": t["range"],
                "size": t["size"],
                "entries": [t],
            })
    out.sort(key=lambda g: (-len(g["entries"]), g["label"]))
    for g in out:
        g.pop("key")
    return out
