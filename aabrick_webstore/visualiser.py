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

# Tiles whose cut texture is wrong even though it is clean. See the note above.
SKIP = []


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
        label, _s, _f, grade = describe_group(r.item_group)
        out.append({
            "code": r.item_code,
            "name": r.web_item_name or r.item_code,
            "route": "/" + (r.route or ""),
            "group": label + (" (B Grade)" if grade else ""),
            "image": image,
            "thumb": textures.thumb_url(r.item_code),
            "w": int(m.group(1)),
            "h": int(m.group(2)),
            "price": r.price_list_rate,
        })

    # Grouped by range, and by code inside it, so the picker reads as the
    # catalogue does rather than in whatever order the database answered.
    out.sort(key=lambda t: (t["group"], t["code"]))
    return out
