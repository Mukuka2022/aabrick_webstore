"""Create the Website Text settings page and fill it with what is on the
site today.

Seeded rather than left blank so the form shows the real sentences and they
are edited in place. A field cleared back to empty falls through to the
wording in site_copy.py, so nobody can empty the page by deleting a box.

    bench --site SITE execute aabrick_webstore.setup_text.run

Safe to run twice.
"""

import frappe

from aabrick_webstore.site_copy import COPY, LONG

DT = "Website Text"
MODULE = "Aabrick Webstore"


def _fields():
    out = []
    for key, label, default, helptext in COPY:
        if key.startswith("sec_"):
            out.append({"fieldname": key, "label": label,
                        "fieldtype": "Section Break"})
            continue
        f = {
            "fieldname": key,
            "label": label,
            "fieldtype": "Small Text" if key in LONG else "Data",
        }
        if helptext:
            f["description"] = helptext
        out.append(f)
    return out


def run():
    if frappe.db.exists("DocType", DT):
        _sync()
    else:
        frappe.get_doc({
            "doctype": "DocType", "name": DT, "module": MODULE,
            "issingle": 1, "track_changes": 1,
            "fields": _fields(),
            "permissions": [
                {"role": "Website Manager", "read": 1, "write": 1, "create": 1},
                {"role": "System Manager", "read": 1, "write": 1, "create": 1},
            ],
        }).insert(ignore_permissions=True)
        print("  created %s" % DT)

    _seed()
    frappe.db.commit()
    frappe.clear_cache()
    print("  open it at /app/website-text")


def _sync():
    doc = frappe.get_doc("DocType", DT)
    have = {f.fieldname for f in doc.fields}
    added = [f for f in _fields() if f["fieldname"] not in have]
    if not added:
        print("  %s is already up to date" % DT)
        return
    for f in added:
        doc.append("fields", f)
    doc.save(ignore_permissions=True)
    print("  added %d field(s) to %s" % (len(added), DT))


def _seed():
    """Put today's wording in, without overwriting anything already edited."""
    doc = frappe.get_single(DT)
    filled = 0
    for key, _label, default, _help in COPY:
        if default is None:
            continue
        if not (doc.get(key) or "").strip():
            doc.set(key, default)
            filled += 1
    if filled:
        doc.save(ignore_permissions=True)
        print("  filled %d field(s) with the wording on the site today" % filled)
    else:
        print("  every field already has something in it")
