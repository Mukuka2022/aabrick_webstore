"""Unpublish the old website pages, keeping only the two calculators.

The current homepage is kept published deliberately: Website Settings points
home_page at /home, so unpublishing it before a replacement exists would 404
the site root.

    bench --site www.aabrick.com execute aabrick_webstore.pagecleanup.preview
    bench --site www.aabrick.com execute aabrick_webstore.pagecleanup.apply_all
"""

import frappe

# routes that stay live
KEEP = {
    "tile-calculator",          # keep, to be redesigned
    "pvc-ceiling-calculater",   # keep, to be redesigned (note the misspelling)
    "home",                     # temporary: site root until a new homepage exists
}


def _pages():
    web = frappe.get_all("Web Page",
                         filters={"published": 1},
                         fields=["name", "route", "title"],
                         order_by="route")
    builder = frappe.get_all("Builder Page",
                             filters={"published": 1},
                             fields=["name", "route", "page_title"],
                             order_by="route")
    return web, builder


def preview():
    web, builder = _pages()
    home = frappe.db.get_single_value("Website Settings", "home_page")

    print("=" * 68)
    print("PAGE CLEANUP - PREVIEW")
    print("=" * 68)
    print("Website Settings home_page = %s\n" % home)

    print("KEEP published (%d):" % len(KEEP))
    for p in web:
        if p.route in KEEP:
            why = "site root - replace before unpublishing" if p.route == "home" \
                  else "calculator, to be redesigned"
            print("   = %-28s %-22s %s" % (p.route, p.title, why))

    drop_web = [p for p in web if p.route not in KEEP]
    print("\nUNPUBLISH Web Pages (%d):" % len(drop_web))
    for p in drop_web:
        print("   - %-28s %s" % (p.route, p.title))

    print("\nUNPUBLISH Builder Pages (%d):" % len(builder))
    for p in builder:
        print("   - %-28s %s" % (p.route, p.page_title))

    print("\ntotal pages to unpublish: %d" % (len(drop_web) + len(builder)))
    return len(drop_web) + len(builder)


def apply_all():
    web, builder = _pages()
    done, errors = 0, []

    for p in web:
        if p.route in KEEP:
            continue
        try:
            frappe.db.set_value("Web Page", p.name, "published", 0)
            done += 1
        except Exception as e:
            errors.append(("Web Page", p.route, str(e)[:90]))

    for p in builder:
        try:
            frappe.db.set_value("Builder Page", p.name, "published", 0)
            done += 1
        except Exception as e:
            errors.append(("Builder Page", p.route, str(e)[:90]))

    frappe.db.commit()
    frappe.clear_cache()

    print("pages unpublished : %d" % done)
    print("errors            : %d" % len(errors))
    for dt, route, err in errors[:10]:
        print("   FAIL %-14s %-24s %s" % (dt, route, err))

    still = frappe.get_all("Web Page", filters={"published": 1}, pluck="route")
    stillb = frappe.get_all("Builder Page", filters={"published": 1}, pluck="route")
    print("\nstill published:")
    for r in sorted(still) + sorted(stillb):
        print("   %s" % r)
    return done


def clear_head_html():
    """Empty the hand-pasted JavaScript and CSS in Website Settings.

    The mobile filter toggle it contained is worth keeping, so it moves into
    webstore.js where it is versioned. The account drawer for /me goes: it
    targets a portal page we are replacing.
    """
    current = frappe.db.get_single_value("Website Settings", "head_html") or ""
    print("head_html was %d characters" % len(current))
    if current:
        # keep a copy on disk in case anything in there was load-bearing
        path = "/tmp/head_html_backup.html"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(current)
        print("backed up to %s" % path)
    frappe.db.set_single_value("Website Settings", "head_html", "")
    frappe.db.commit()
    frappe.clear_cache()
    print("head_html is now empty")
    return len(current)
