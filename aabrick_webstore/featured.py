"""Let AABrick choose the products on the home page.

The row used to pick itself: the dearest published item from each range. That
is a decent default and it stays as the fallback, but it cannot be argued
with, and which four things sit on the front page is a commercial decision
rather than a query.

A tick on the product, not a list of slots in a settings page. It is where
somebody editing a product expects to find it, there is nothing to keep in
step with the catalogue, and unpublishing a product takes it off the home page
without anybody having to remember a second place.

    bench --site SITE execute aabrick_webstore.featured.run

Safe to run twice.
"""

import frappe

DT = "Website Item"
FIELD = "custom_on_home"
LABEL = "Show on the home page"

DESCRIPTION = (
    "The home page shows four products. Tick the ones that should be there.\n\n"
    "Tick nothing and it chooses for itself: the dearest published item from "
    "each range, so the row shows the spread of the catalogue.\n\n"
    "Tick more than four and the four with the highest Ranking win, then the "
    "dearest. A product needs to be published and to have a photograph, or it "
    "cannot appear."
)


def run():
    name = "%s-%s" % (DT, FIELD)
    if frappe.db.exists("Custom Field", name):
        existing = frappe.get_doc("Custom Field", name)
        if existing.description != DESCRIPTION or existing.label != LABEL:
            existing.label = LABEL
            existing.description = DESCRIPTION
            existing.save(ignore_permissions=True)
            print("  updated the wording on %s" % name)
        else:
            print("  %s already has the home page tick" % DT)
    else:
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": DT,
            "fieldname": FIELD,
            "label": LABEL,
            "fieldtype": "Check",
            # Beside Ranking, which is what orders them once more than four
            # are ticked.
            "insert_after": "ranking",
            "description": DESCRIPTION,
        }).insert(ignore_permissions=True)
        print("  added the home page tick to %s" % DT)

    frappe.db.commit()
    frappe.clear_cache()
    print("  tick it on a product at /app/website-item")


def check():
    """What the home page will show, and why."""
    from aabrick_webstore.www.index import FEATURED_COUNT, _auto, _picked

    picked = _picked()
    if picked:
        print("  %d product(s) ticked, showing %d:"
              % (len(picked), min(len(picked), FEATURED_COUNT)))
        for r in picked:
            print("    %-12s ranking %-4s %s"
                  % (r.item_code, r.get("ranking"), r.item_group))
    else:
        print("  nothing ticked, so the row is choosing for itself:")
        for r in _auto():
            print("    %-12s %s" % (r.item_code, r.item_group))
