"""Spell it Matt, not Matte.

Four item groups used "Matte" while four others already used "Matt", which
splits the same product line across two spellings in the catalogue, in the
page titles the product template derives from the group, and in anything a
customer searches for.

This is data, so it does not travel with a git deploy. It lives in the app as
a script rather than as a set of manual edits so the same change can be run
against the live site, and it is idempotent: a second run finds nothing to do.

    bench --site www.aabrick.com execute aabrick_webstore.rename_matt.run
    bench --site www.aabrick.com execute aabrick_webstore.rename_matt.check
"""

import frappe

OLD = "Matte"
NEW = "Matt"


def _targets():
    return frappe.db.sql(
        """SELECT name, route FROM `tabItem Group`
           WHERE name LIKE %s ORDER BY name""",
        ("%" + OLD + "%",),
        as_dict=True,
    )


def check():
    rows = _targets()
    if not rows:
        print("Nothing spelled %s remains." % OLD)
    for g in rows:
        print("   %-46s route=%s  items=%d  web=%d"
              % (g.name, g.route or "(none)", frappe.db.count("Item", {"item_group": g.name}),
                 frappe.db.count("Website Item", {"item_group": g.name})))
    return rows


def run():
    rows = _targets()
    if not rows:
        print("Nothing to rename.")
        return

    for g in rows:
        new_name = g.name.replace(OLD, NEW)
        if frappe.db.exists("Item Group", new_name):
            print("SKIP  %s -> %s already exists" % (g.name, new_name))
            continue

        items = frappe.db.count("Item", {"item_group": g.name})
        web = frappe.db.count("Website Item", {"item_group": g.name})

        frappe.rename_doc("Item Group", g.name, new_name, force=True)

        # The route is a separate field and rename_doc leaves it alone, so the
        # slug would keep saying matte while the name said matt.
        old_route = g.route or ""
        new_route = old_route.replace(OLD.lower(), NEW.lower())
        if new_route and new_route != old_route:
            frappe.db.set_value("Item Group", new_name, "route", new_route, update_modified=False)
            _redirect(old_route, new_route)

        after_items = frappe.db.count("Item", {"item_group": new_name})
        after_web = frappe.db.count("Website Item", {"item_group": new_name})
        print("%s\n   -> %s" % (g.name, new_name))
        print("      items %d -> %d, website items %d -> %d" % (items, after_items, web, after_web))
        if new_route != old_route:
            print("      route %s -> %s  (redirect added)" % (old_route, new_route))

    frappe.db.commit()
    print()
    print("Now run: bench --site <site> clear-cache")


def _redirect(source, target):
    """Old URLs keep working. Nothing is indexed yet, but a 404 is a 404."""
    src = "/" + source.lstrip("/")
    tgt = "/" + target.lstrip("/")
    settings = frappe.get_doc("Website Settings")
    for row in settings.route_redirects:
        if (row.source or "").rstrip("/") == src.rstrip("/"):
            return
    settings.append("route_redirects", {"source": src, "target": tgt})
    settings.flags.ignore_permissions = True
    settings.save()
