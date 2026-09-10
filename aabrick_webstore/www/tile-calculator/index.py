"""The tile calculator.

The old page asked a customer to type the tile size, the pieces per box and the
price. All three are already known, so the calculator now offers the catalogue
and fills them in: size from the item group, piece count from the item
description, price from the Web Price List.

The piece count was checked before being relied on. Across 424 items it lands
on real box sizes, 1.44 m2 for 600x600 at 4 pieces, for 600x1200 at 2 and for
300x600 at 8, and 1.28 for 800x800 at 2. Fourteen items disagree with their own
range, claiming a 0.36 m2 box, so they are offered without a piece count rather
than with a wrong one, and the field falls back to manual entry.
"""

import re

import frappe

from aabrick_webstore.overrides.website_item import describe_group

PC = re.compile(r"(\d+)\s*PC", re.I)
SIZE = re.compile(r"\((\d+)\s*[xX]\s*(\d+)\)")

# A tile box is between roughly one and two square metres. Anything outside
# that is a description that disagrees with its own range.
MIN_BOX_M2 = 0.9
MAX_BOX_M2 = 2.2

no_cache = 1
sitemap = 1


def get_context(context):
    context.title = "Tile Calculator | AABrick Zambia"
    context.aab_description = (
        "Work out how many boxes of tiles you need. Pick a tile from the AABrick "
        "range and the size, pieces per box and price fill in themselves, or enter "
        "your own figures."
    )
    context.aab_canonical = frappe.utils.get_url("/tile-calculator")
    context.aab_tiles = _tiles()
    context.aab_tiles_json = frappe.as_json(context.aab_tiles)
    context.aab_branch_count = frappe.db.count("Branch Location") or 46
    # The same cache buster the stylesheet uses, so the script cannot go
    # stale against a page that has changed.
    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context


def _tiles():
    rows = frappe.db.sql(
        """
        SELECT w.item_code, w.route, w.item_group, i.description,
               ip.price_list_rate
        FROM `tabWebsite Item` w
        JOIN `tabItem` i ON i.name = w.item_code
        LEFT JOIN `tabItem Price` ip
          ON ip.item_code = w.item_code AND ip.price_list = 'Web Price List'
        WHERE w.published = 1 AND w.item_group LIKE '%%Tiles%%'
        ORDER BY w.item_group, w.item_code
        """,
        as_dict=True,
    )

    out = []
    for r in rows:
        size = SIZE.search(r.item_group or "")
        if not size:
            continue
        w_mm, h_mm = int(size.group(1)), int(size.group(2))

        pcs = None
        m = PC.search(r.description or "")
        if m:
            n = int(m.group(1))
            box_m2 = n * (w_mm / 1000.0) * (h_mm / 1000.0)
            if MIN_BOX_M2 <= box_m2 <= MAX_BOX_M2:
                pcs = n

        label, _s, _f, grade = describe_group(r.item_group)
        out.append({
            "code": r.item_code,
            "route": "/" + (r.route or ""),
            "group": label + (" (B Grade)" if grade else ""),
            "w": w_mm,
            "h": h_mm,
            "pcs": pcs,
            "price": r.price_list_rate,
        })
    return out
