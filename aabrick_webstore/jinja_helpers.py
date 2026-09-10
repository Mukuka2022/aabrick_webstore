"""Data for the navbar and the footer.

Frappe's navbar is built from Website Settings rows, which is fine for a menu
somebody types out once. Ours has to carry eleven tile ranges and four guides
and stay right as the catalogue changes, so it is read from the catalogue on
each render instead, and exposed to the templates as a Jinja method.

Cached per request: the navbar and the footer both ask for it on every page.
"""

import frappe

PHONE = "+260 960 787 777"


def nav_data():
    cached = getattr(frappe.local, "_aab_nav", None)
    if cached is not None:
        return cached

    data = frappe._dict({
        "phone": PHONE,
        "phone_link": PHONE.replace(" ", ""),
        "ranges": _ranges(),
        "guides": _guides(),
        "branch_count": frappe.db.count("Branch Location") or 46,
        "year": frappe.utils.now_datetime().year,
    })
    frappe.local._aab_nav = data
    return data


def _ranges():
    """A grade tile ranges, biggest first, plus the two other lines we sell
    online. B grade is reached from its A grade twin rather than doubling the
    length of every menu."""
    from aabrick_webstore.overrides.item_group import _plural
    from aabrick_webstore.overrides.website_item import describe_group

    rows = frappe.db.sql(
        """
        SELECT g.name, g.route, COUNT(w.name) n
        FROM `tabItem Group` g
        JOIN `tabWebsite Item` w ON w.item_group = g.name AND w.published = 1
        WHERE g.is_group = 0 AND g.show_in_website = 1 AND IFNULL(g.route, '') <> ''
        GROUP BY g.name ORDER BY n DESC
        """,
        as_dict=True,
    )

    out = []
    for r in rows:
        label, size, _finish, grade = describe_group(r.name)
        if grade:
            continue
        out.append(frappe._dict({
            "label": _plural(label),
            "route": "/" + r.route,
            "count": r.n,
            "size": size,
        }))
    return out


def _guides():
    try:
        from aabrick_webstore.www.guides.index import guides

        return guides()
    except Exception:
        return []
