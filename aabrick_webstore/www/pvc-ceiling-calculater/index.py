"""The PVC ceiling calculator.

Unlike the tile calculator this cannot offer the catalogue, because none of the
74 PVC boards in the ERP are published to the website. What the ERP does show
is that they are sold by the board, in Unit, and that every Standard Selling
rate is exactly the board's area at 100 ZMW per square metre: a 4m by 250mm
board is 100, a 4m by 300mm is 120, 5m by 300mm is 150, 6m by 250mm is 150 and
6m by 300mm is 180.

So the page offers the sizes that actually exist rather than asking a customer
to measure a board, and prices them from that rate while making clear it is a
guide until the boards are on the website.
"""

import frappe

no_cache = 1
sitemap = 1

# Width in mm, length in m. Taken from the item codes, each of which prices at
# its own area, so these are the sizes on the shelf rather than a guess.
BOARDS = [
    {"w": 250, "l": 4.0},
    {"w": 250, "l": 5.0},
    {"w": 250, "l": 6.0},
    {"w": 300, "l": 4.0},
    {"w": 300, "l": 5.0},
    {"w": 300, "l": 6.0},
]

RATE_PER_M2 = 100.0


def get_context(context):
    context.title = "PVC Ceiling Calculator | AABrick Zambia"
    context.aab_description = (
        "Work out how many PVC ceiling boards you need. Enter the room or the "
        "square metres, choose a board size, and this counts the boards and "
        "estimates the cost."
    )
    context.aab_canonical = frappe.utils.get_url("/pvc-ceiling-calculater")

    boards = []
    for b in BOARDS:
        area = (b["w"] / 1000.0) * b["l"]
        boards.append({
            "w": b["w"],
            "l": b["l"],
            "area": round(area, 3),
            "price": round(area * RATE_PER_M2, 2),
            "label": "%dmm x %sm" % (b["w"], ("%g" % b["l"])),
        })
    context.aab_boards = boards
    context.aab_boards_json = frappe.as_json(boards)
    context.aab_rate = RATE_PER_M2
    context.aab_branch_count = frappe.db.count("Branch Location") or 46

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
