"""The headings on the login page, in AABrick's own words.

Two things were wrong with them. The stored name is "AAbrick Portal",
with a small b, and frappe builds the headings around it with the article
written into the string:

    Login to AAbrick Portal
    Create a AAbrick Portal Account

Correcting the spelling leaves "a AABrick", which is still wrong: the
name is said ay-ay-brick, so English wants "an". The article cannot be
reached from here, and neither can the macro that writes the heading, so
the headings are replaced with wording of our own that sidesteps the
question and says something plainer anyway.

The stored name is corrected too, because it is on the emails frappe
sends and in the browser tab, where nothing here reaches.
"""

import frappe

NAME = "AABrick"


def run():
    old = frappe.db.get_single_value("Website Settings", "app_name")
    if old != NAME:
        frappe.db.set_single_value("Website Settings", "app_name", NAME)
        frappe.db.commit()
        frappe.clear_cache()
        print("  app_name: %r -> %r" % (old, NAME))
    else:
        print("  app_name already %r" % NAME)
    print("  (the headings on the login page itself are set by nav.js)")
