"""Two published tiles pointed at photographs that are not on disk.

A B-grade tile is the same design as its A-grade twin, only the grade
differs, so the twin's photograph is the honest picture to show. Where the
twin has no photograph either, the tile comes off the site rather than
staying up with an empty box where the tile should be.

    bench --site SITE execute aabrick_webstore.fix_missing_images.run

Safe to run twice.
"""

import os

import frappe


def _on_disk(url):
    if not url:
        return False
    return os.path.exists(os.path.join(frappe.get_site_path("public"), url.lstrip("/")))


def _twin(code):
    """The A-grade item a D code was cut from: 96000D came from 96000."""
    if not code.endswith("D"):
        return None
    return frappe.db.get_value(
        "Website Item", {"item_code": code[:-1]}, ["item_code", "website_image"],
        as_dict=True,
    )


def run():
    broken = frappe.db.sql(
        """
        select name, item_code, website_image
        from `tabWebsite Item`
        where published = 1 and ifnull(website_image, '') != ''
        """,
        as_dict=True,
    )
    broken = [r for r in broken if not _on_disk(r.website_image)]

    if not broken:
        print("  nothing published points at a missing photograph")
        return

    for r in broken:
        twin = _twin(r.item_code)
        if twin and _on_disk(twin.website_image):
            frappe.db.set_value("Website Item", r.name, "website_image", twin.website_image)
            print("  %-8s now shows %s, the photograph of its A grade twin %s"
                  % (r.item_code, twin.website_image, twin.item_code))
        else:
            frappe.db.set_value("Website Item", r.name, "published", 0)
            why = "the twin has no photograph either" if twin else "it has no A grade twin"
            print("  %-8s unpublished: %s" % (r.item_code, why))

    frappe.db.commit()
    frappe.clear_cache()

    left = [r for r in frappe.db.sql(
        """
        select item_code, website_image from `tabWebsite Item`
        where published = 1 and ifnull(website_image, '') != ''
        """, as_dict=True) if not _on_disk(r.website_image)]
    print()
    print("  published tiles still missing a photograph:", len(left))
