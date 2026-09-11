import frappe


def run():
    for dt, name in (("Web Page", "aab-theme-test-page"),
                     ("Blog Post", "aab-theme-test-post"),
                     ("Blog Category", "aab-test")):
        print("  %-14s %-22s %s" % (dt, name,
                                    "STILL THERE" if frappe.db.exists(dt, name) else "gone"))
