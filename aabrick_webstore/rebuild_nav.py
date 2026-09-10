"""Rebuild the navigation around the pages that actually exist.

The menu was pointing at six pages that are unpublished, so every one of them
was a dead link: /home, about-us, /wall-tiles, /floor-tiles, /tile-fix and
/fertilizers. Four more entries were absolute https://www.aabrick.com/... URLs,
which send a visitor off the site they are on and break entirely on a local or
staging copy. Two named individual job adverts, which go stale on their own.

The tile ranges now come from the item groups, so the menu cannot drift from
the catalogue again: add a group, and the next run picks it up.

    bench --site www.aabrick.com execute aabrick_webstore.rebuild_nav.check
    bench --site www.aabrick.com execute aabrick_webstore.rebuild_nav.run
"""

import frappe

from aabrick_webstore.overrides.item_group import _plural
from aabrick_webstore.overrides.website_item import describe_group

# Pages the client asked to keep. Everything else stays unpublished.
KEEP_PAGES = {"tile-calculator", "pvc-ceiling-calculater"}


def _tile_groups():
    """Published A grade tile ranges, biggest first. The B grade pages are
    reachable from their A grade twin rather than from the menu, which would
    otherwise carry two entries for every size."""
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
        label, _, _, grade = describe_group(r.name)
        if grade:
            continue
        out.append((_plural(label), "/" + r.route, r.n))
    return out


def check():
    ws = frappe.get_doc("Website Settings")
    print("=== current top bar ===")
    dead = 0
    for r in ws.top_bar_items:
        note = ""
        url = (r.url or "").strip()
        if url.startswith("http"):
            note = "  <- absolute url"
        elif url and not url.startswith("/"):
            note = "  <- no leading slash"
        if url:
            route = url.lstrip("/").split("?")[0]
            if route and frappe.db.exists("Web Page", {"route": route}):
                if not frappe.db.get_value("Web Page", {"route": route}, "published"):
                    note = "  <- page is UNPUBLISHED"
                    dead += 1
        print("   %-28s %-46s%s" % (r.label, url or "(group)", note))
    print("   %d entries point at unpublished pages" % dead)

    print()
    print("=== tile ranges available for the menu ===")
    for label, route, n in _tile_groups():
        print("   %-40s %-46s %d" % (label, route, n))

    print()
    print("=== web pages ===")
    for p in frappe.get_all("Web Page", fields=["route", "published", "title"], order_by="route"):
        flag = "PUB" if p.published else "   "
        keep = " (keep)" if p.route in KEEP_PAGES else ""
        print("   %s %-34s %s%s" % (flag, p.route or "-", p.title, keep))


def run():
    _unpublish_pages()
    _rebuild_top_bar()
    _rebuild_footer()
    frappe.db.commit()
    print()
    print("Now run: bench --site <site> clear-cache")


def _unpublish_pages():
    print("=== web pages ===")
    changed = 0
    for p in frappe.get_all("Web Page", fields=["name", "route", "published"]):
        should = p.route in KEEP_PAGES
        if bool(p.published) == should:
            continue
        frappe.db.set_value("Web Page", p.name, "published", 1 if should else 0,
                            update_modified=False)
        print("   %-34s -> %s" % (p.route, "published" if should else "unpublished"))
        changed += 1
    if not changed:
        print("   already correct: only %s published" % ", ".join(sorted(KEEP_PAGES)))


def _rebuild_top_bar():
    ws = frappe.get_doc("Website Settings")
    home = ws.home_page
    ws.set("top_bar_items", [])

    def add(label, url=None, parent=None):
        ws.append("top_bar_items", {
            "label": label,
            "url": url or "",
            "parent_label": parent or "",
        })

    add("Shop")
    add("All Products", "/all-products", "Shop")
    for label, route, _n in _tile_groups():
        add(label, route, "Shop")

    add("Calculators")
    add("Tile Calculator", "/tile-calculator", "Calculators")
    add("PVC Ceiling Calculator", "/pvc-ceiling-calculater", "Calculators")

    add("Branches", "/branches")

    add("Support")
    add("Contact Us", "/contact", "Support")
    add("Careers", "/jobs", "Support")

    add("Cart", "/cart")

    ws.flags.ignore_permissions = True
    ws.save()
    if ws.home_page != home:
        frappe.db.set_single_value("Website Settings", "home_page", home or "index")

    print()
    print("=== top bar ===")
    for r in ws.top_bar_items:
        print("   %-28s %s" % (r.label, r.url or "(group)"))


def _rebuild_footer():
    ws = frappe.get_doc("Website Settings")
    home = ws.home_page
    ws.set("footer_items", [])
    for label, url in (
        ("All Products", "/all-products"),
        ("Branches", "/branches"),
        ("Tile Calculator", "/tile-calculator"),
        ("PVC Ceiling Calculator", "/pvc-ceiling-calculater"),
        ("Contact Us", "/contact"),
    ):
        ws.append("footer_items", {"label": label, "url": url})
    ws.flags.ignore_permissions = True
    ws.save()
    if ws.home_page != home:
        frappe.db.set_single_value("Website Settings", "home_page", home or "index")

    print()
    print("=== footer ===")
    for r in ws.footer_items:
        print("   %-28s %s" % (r.label, r.url))
