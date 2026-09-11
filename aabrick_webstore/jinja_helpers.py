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


def site_images():
    """Pictures somebody at AABrick can change, without a terminal.

    Everything here is optional. A page with no picture set keeps the plain
    heading it has now, and the home page falls back to the photograph that
    ships in the app, so a fresh install looks like this one before anybody
    has uploaded anything.

    Cached per request: a page head, the hero and the gallery would
    otherwise read the same single doctype three times.
    """
    cached = getattr(frappe.local, "_aab_images", None)
    if cached is not None:
        return cached

    try:
        s = frappe.get_cached_doc("Website Images")
    except Exception:
        s = None

    def pick(field):
        return (s.get(field) or "").strip() if s else ""

    shots = []
    for i in (1, 2, 3):
        src = pick("shot_%d" % i)
        if src:
            shots.append(frappe._dict({
                "src": src,
                "caption": pick("caption_%d" % i),
                "detail": pick("detail_%d" % i),
            }))

    out = frappe._dict({
        "hero": pick("hero"),
        "hero_mobile": pick("hero_mobile"),
        # The gallery is all three or none. Two reads as one that failed.
        "shots": shots if len(shots) == 3 else [],
        "heads": frappe._dict({
            "all_products": pick("head_all_products"),
            "branches": pick("head_branches"),
            "contact": pick("head_contact"),
            "guides": pick("head_guides"),
            "tile_calculator": pick("head_tile_calculator"),
            "pvc_calculator": pick("head_pvc_calculator"),
        }),
    })

    frappe.local._aab_images = out
    return out
