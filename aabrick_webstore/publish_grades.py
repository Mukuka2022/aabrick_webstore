"""Publish the B grade tiles, and give every stocked group a category page.

Three separate problems, all data, all found together:

1. 205 Website Items sit in the D groups, every one of them with a route and a
   Web Price List rate, and not one of them published. D is the second grade:
   its price is exactly 15 ZMW below the A grade twin in all eleven pairs, and
   the codes are distinct (86000D against 86000), so these are separate SKUs
   rather than duplicates.

2. Three item groups carry a route belonging to a different group. Wall Tiles
   (300X600) and Wall Tiles (300X300) have each other's, and Glazed Porcelain
   Tiles (600X600) has the 600x1200 one. Anyone landing on those would be told
   they are looking at a size they are not.

3. Groups that hold published products mostly have show_in_website off, so the
   category page 404s while its products are live. The largest tile group on
   the site is one of them.

Data does not travel with a git deploy, so this is a script rather than a set
of manual edits, and it is idempotent.

    bench --site www.aabrick.com execute aabrick_webstore.publish_grades.check
    bench --site www.aabrick.com execute aabrick_webstore.publish_grades.run
"""

import re

import frappe

# Route corrections, keyed by group. Written out rather than derived, because
# the slug should keep whatever else it already says and only the size is wrong.
ROUTE_FIXES = {
    "Wall Tiles (300X600) - 36XXX": "tiles/wall-tiles-300x600-36xxx",
    "Wall Tiles (300X300) - 33XXX": "tiles/wall-tiles-300x300-33xxx",
    "Glazed Porcelain Tiles (600X600) - 86XXX": "tiles/glazed-porcelain-tiles-600x600-86xxx",
}


def _d_items(published=None):
    filters = {"item_group": ["like", "% D (%"]}
    if published is not None:
        filters["published"] = published
    return frappe.get_all(
        "Website Item", filters=filters,
        fields=["name", "item_code", "item_group", "website_image", "route"],
    )


def check():
    d = _d_items()
    print("D website items      : %d" % len(d))
    print("   published         : %d" % len([x for x in d if frappe.db.get_value(
        "Website Item", x.name, "published")]))
    print("   without an image  : %d" % len([x for x in d if not x.website_image]))

    print()
    print("routes still wrong   :")
    wrong = 0
    for group, route in ROUTE_FIXES.items():
        current = frappe.db.get_value("Item Group", group, "route")
        if current != route:
            wrong += 1
            print("   %-46s %s" % (group[:46], current))
    if not wrong:
        print("   none")

    print()
    print("groups with published products and no category page:")
    hidden = _hidden_groups()
    for g in hidden:
        print("   %-46s %d products" % (g[0][:46], g[1]))
    if not hidden:
        print("   none")


def _hidden_groups():
    rows = frappe.db.sql(
        """
        SELECT g.name, COUNT(w.name) n
        FROM `tabItem Group` g
        JOIN `tabWebsite Item` w ON w.item_group = g.name AND w.published = 1
        WHERE g.is_group = 0 AND IFNULL(g.show_in_website, 0) = 0
        GROUP BY g.name ORDER BY n DESC
        """
    )
    return rows


def run():
    _fix_routes()
    _publish_d()
    _show_categories()
    frappe.db.commit()
    print()
    print("Now run: bench --site <site> clear-cache")


def _fix_routes():
    print("=== routes ===")
    changed = 0
    for group, route in ROUTE_FIXES.items():
        if not frappe.db.exists("Item Group", group):
            print("   SKIP %s does not exist" % group)
            continue
        current = frappe.db.get_value("Item Group", group, "route")
        if current == route:
            continue
        if frappe.db.exists("Item Group", {"route": route}):
            print("   SKIP %s: %s is already taken" % (group, route))
            continue
        frappe.db.set_value("Item Group", group, "route", route, update_modified=False)
        _redirect(current, route)
        print("   %-46s %s -> %s" % (group[:46], current, route))
        changed += 1
    if not changed:
        print("   nothing to correct")


def _publish_d():
    print()
    print("=== B grade items ===")
    todo = _d_items(published=0)
    if not todo:
        print("   already published")
        return

    published = skipped = 0
    for row in todo:
        if not row.website_image:
            # A product with no picture is worse than one that is not listed.
            print("   SKIP %s has no image" % row.item_code)
            skipped += 1
            continue
        frappe.db.set_value("Website Item", row.name, "published", 1, update_modified=False)
        published += 1
    print("   published %d, skipped %d" % (published, skipped))


def _show_categories():
    print()
    print("=== category pages ===")
    hidden = _hidden_groups()
    if not hidden:
        print("   every group holding published products already has one")
        return
    for name, n in hidden:
        frappe.db.set_value("Item Group", name, "show_in_website", 1, update_modified=False)
        print("   %-46s now shown (%d products)" % (name[:46], n))


def _redirect(source, target):
    if not source or not target or source == target:
        return
    src = "/" + source.lstrip("/")
    tgt = "/" + target.lstrip("/")
    settings = frappe.get_doc("Website Settings")
    home = settings.home_page
    for row in settings.route_redirects:
        if (row.source or "").rstrip("/") == src.rstrip("/"):
            return
    settings.append("route_redirects", {"source": src, "target": tgt})
    settings.flags.ignore_permissions = True
    settings.save()
    # Saving this doctype has cleared home_page before now, which drops the
    # whole site to the login page for a guest.
    if settings.home_page != home:
        frappe.db.set_single_value("Website Settings", "home_page", home or "index")
