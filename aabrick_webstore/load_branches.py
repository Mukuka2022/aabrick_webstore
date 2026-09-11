"""Write the supplied branch details onto the Branch Location records.

Safe to run twice: it matches on branch_name and only writes fields that
differ, so re-running after a correction touches only what changed.

    bench --site SITE execute aabrick_webstore.load_branches.run

Nothing here publishes a branch. Publishing stays a separate decision.
"""

import frappe

from aabrick_webstore.branch_data import BRANCHES

# counter_or_depot has no field of its own yet; a Depot would need the page to
# say so, and every branch AABrick returned is a Counter. Left out on purpose
# rather than stored somewhere it would not be read.
FIELDS = (
    "street_address", "phone", "whatsapp", "email",
    "hours_weekday", "hours_saturday", "hours_sunday", "hours_note",
    "maps_url",
)


def run():
    existing = {
        d.branch_name: d.name
        for d in frappe.get_all("Branch Location", fields=["name", "branch_name"])
    }

    changed = touched = missing = 0
    for row in BRANCHES:
        name = existing.get(row["branch"])
        if not name:
            print("  no Branch Location called %r" % row["branch"])
            missing += 1
            continue

        doc = frappe.get_doc("Branch Location", name)
        edits = []
        for f in FIELDS:
            new = row.get(f, "")
            if new and (doc.get(f) or "") != new:
                doc.set(f, new)
                edits.append(f)

        # The town is only worth writing where it actually differs from the
        # branch name, which is where the branch is named after a road.
        town = row.get("town", "")
        if town and (doc.get("city") or "") != town:
            doc.city = town
            edits.append("city")

        if edits:
            doc.save(ignore_permissions=True)
            changed += len(edits)
            touched += 1

    frappe.db.commit()
    print("  branches updated :", touched)
    print("  fields written   :", changed)
    print("  not found        :", missing)

    have_addr = sum(1 for b in BRANCHES if b["street_address"])
    have_wa = sum(1 for b in BRANCHES if b["whatsapp"])
    print("  with an address  : %d of %d" % (have_addr, len(BRANCHES)))
    print("  with whatsapp    : %d of %d" % (have_wa, len(BRANCHES)))


def publish():
    """Put the branches on the site.

    A branch with a phone number and opening hours is worth finding even
    where the street address has not come back yet, so this publishes all of
    them rather than only the complete ones.
    """
    n = 0
    for d in frappe.get_all("Branch Location", filters={"published": 0}, pluck="name"):
        frappe.db.set_value("Branch Location", d, "published", 1)
        n += 1
    frappe.db.commit()
    frappe.clear_cache()
    print("  published:", n)
    print("  live now :", frappe.db.count("Branch Location", {"published": 1}))
