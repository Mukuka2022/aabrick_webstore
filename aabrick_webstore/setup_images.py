"""Create the Website Images settings page, and give branches a photograph.

The pictures on this site were set by running a bench command, which means
nobody at AABrick could change one. These fields put them in the desk
instead: upload, save, the page changes.

They are stored as site files rather than in the app, deliberately and
against how hero.py works. A photograph uploaded on the live server has to
survive the next git pull, and that is the line between code and data
AABrick has already drawn. The app images stay as the fallback, so a fresh
install still looks like this one before anybody uploads anything.

    bench --site SITE execute aabrick_webstore.setup_images.run

Safe to run twice.
"""

import frappe

DT = "Website Images"
MODULE = "Aabrick Webstore"


def _f(fieldname, label, fieldtype="Attach Image", **kw):
    d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
    d.update(kw)
    return d


FIELDS = [
    _f("sec_hero", "Home page", "Section Break"),
    _f("hero", "Hero photograph",
       description="The big picture behind the words on the home page. "
                   "Wide, about 2400 by 1100. Dark or busy is fine: the "
                   "page lays a dark wash over it so the words stay "
                   "readable."),
    _f("hero_mobile", "Hero photograph, phone",
       description="Optional. A taller crop of the same scene, about 900 "
                   "by 1000. A wide picture on a phone becomes a slit too "
                   "shallow to read. Left empty, the wide one is used."),

    _f("sec_shots", "Finished with AABrick", "Section Break",
       description="Three photographs of rooms. The section only appears "
                   "when all three are set: a gallery of one reads as "
                   "something half broken."),
    _f("shot_1", "Photograph 1"),
    _f("caption_1", "Caption 1", "Data",
       description="Where it is. For example: Sitting room, Kitwe"),
    _f("detail_1", "Detail 1", "Data",
       description="Optional. What is on the floor. For example: Tile 86072"),
    _f("col_shots_1", "", "Column Break"),
    _f("shot_2", "Photograph 2"),
    _f("caption_2", "Caption 2", "Data"),
    _f("detail_2", "Detail 2", "Data"),
    _f("col_shots_2", "", "Column Break"),
    _f("shot_3", "Photograph 3"),
    _f("caption_3", "Caption 3", "Data"),
    _f("detail_3", "Detail 3", "Data"),

    _f("sec_heads", "Beside the page titles", "Section Break",
       description="One picture per page, shown next to the heading. Each "
                   "is optional: a page with none keeps the plain heading "
                   "it has now. Landscape, about 1200 by 800."),
    _f("head_all_products", "All products"),
    _f("head_branches", "Branches"),
    _f("head_contact", "Contact"),
    _f("col_heads", "", "Column Break"),
    _f("head_guides", "Guides"),
    _f("head_tile_calculator", "Tile calculator"),
    _f("head_pvc_calculator", "PVC ceiling calculator"),
]


def run():
    if frappe.db.exists("DocType", DT):
        _sync_fields()
    else:
        frappe.get_doc({
            "doctype": "DocType",
            "name": DT,
            "module": MODULE,
            "issingle": 1,
            "custom": 0,
            "track_changes": 1,
            "fields": FIELDS,
            "permissions": [{
                "role": "Website Manager",
                "read": 1, "write": 1, "create": 1,
            }, {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1,
            }],
        }).insert(ignore_permissions=True)
        print("  created %s" % DT)

    _branch_photo()
    frappe.db.commit()
    frappe.clear_cache()
    print("  open it at /app/website-images")


def _sync_fields():
    """Add any field the doctype does not have yet, leaving the rest alone."""
    doc = frappe.get_doc("DocType", DT)
    have = {f.fieldname for f in doc.fields}
    added = [f for f in FIELDS if f["fieldname"] not in have]
    if not added:
        print("  %s is already up to date" % DT)
        return
    for f in added:
        doc.append("fields", f)
    doc.save(ignore_permissions=True)
    print("  added %d field(s) to %s" % (len(added), DT))


def _branch_photo():
    """A photograph of the shopfront, which is how people recognise a shop."""
    if frappe.db.exists("Custom Field", "Branch Location-photo"):
        print("  Branch Location already has a photo field")
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Branch Location",
        "fieldname": "photo",
        "label": "Photograph",
        "fieldtype": "Attach Image",
        "insert_after": "street_address",
        "description": "The shopfront as somebody walking up to it would "
                       "see it. This is what tells a customer they have "
                       "found the right place.",
    }).insert(ignore_permissions=True)
    print("  added a photo field to Branch Location")
