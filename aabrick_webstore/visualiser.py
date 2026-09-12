"""The tiles the visualiser can actually lay, and the rooms it lays them in.

A tile only works as a floor texture if it is square, big enough to hold
up when it is stretched across a room, and free of the supplier's name.
Marcopolo prints "MARCOPOLO TILES" and the code across the top left of
most of its catalogue shots in orange, which is fine on a product card and
impossible on a floor: it repeats every 600mm.

Of 435 published items, 218 are square and at least 600px. 189 of those
carry the label. The 29 left are listed here, found by counting saturated
orange pixels in the top left of every image and checked by eye.

The list is code rather than a query because it is a judgement about
photographs, and the answer must not change quietly when somebody
re-uploads an image. When AABrick get clean files from Marcopolo this list
is where they go.

Sizes come from the item group, which spells them out: (600X600),
(800X800), (300X300). That is what lets a tile lay at true scale rather
than at whatever size looks about right.
"""

import re

import frappe

from aabrick_webstore.overrides.website_item import describe_group

SIZE = re.compile(r"\((\d+)\s*[xX]\s*(\d+)\)")

# Square, 600px or better, and no supplier name burnt into the picture.
USABLE = [
    "96000D", "96202", "96203", "96201", "96206", "96204", "96207",
    "33000", "86008", "88008", "86001", "86003", "89301", "96060",
    "96000", "56111", "96025", "86087", "86086", "86085", "86084",
    "86083", "86082", "86081", "86080", "88009D", "88009",
]


def tiles():
    """The usable tiles, with everything the page needs to draw them."""
    if not USABLE:
        return []

    rows = frappe.db.sql(
        """
        SELECT w.item_code, w.web_item_name, w.route, w.item_group,
               w.website_image, ip.price_list_rate
        FROM `tabWebsite Item` w
        LEFT JOIN `tabItem Price` ip
          ON ip.item_code = w.item_code AND ip.price_list = 'Web Price List'
        WHERE w.published = 1 AND w.item_code IN (%s)
        """ % ", ".join(["%s"] * len(USABLE)),
        tuple(USABLE),
        as_dict=True,
    )

    out = []
    for r in rows:
        m = SIZE.search(r.item_group or "")
        if not m or not r.website_image:
            continue
        label, _s, _f, grade = describe_group(r.item_group)
        out.append({
            "code": r.item_code,
            "name": r.web_item_name or r.item_code,
            "route": "/" + (r.route or ""),
            "group": label + (" (B Grade)" if grade else ""),
            "image": r.website_image,
            "w": int(m.group(1)),
            "h": int(m.group(2)),
            "price": r.price_list_rate,
        })

    order = {c: i for i, c in enumerate(USABLE)}
    out.sort(key=lambda t: order.get(t["code"], 999))
    return out
