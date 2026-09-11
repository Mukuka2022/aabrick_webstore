"""The wording is unchanged, an edit reaches the page, and clearing a field
puts the original sentence back.
"""

import frappe
import frappe.website.serve


def _home():
    frappe.local._aab_nav = None
    frappe.local._aab_text = None
    frappe.clear_cache()
    return frappe.website.serve.get_response_content("index")


def run():
    html = _home()
    print("=== the page still says what it said ===")
    for line in ("Premium building &amp; finishing materials",
                 "Building Zambia", "Beautifully",
                 "Find what you need", "Popular right now",
                 "Twenty years supplying Zambia",
                 "There is a branch near you",
                 "However you prefer to buy",
                 "Your finishing needs, a click away",
                 "branches nationwide"):
        print("  %-44s %s" % (line[:44], "yes" if line in html else "NO"))

    print()
    print("=== an edit reaches the page ===")
    doc = frappe.get_single("Website Text")
    was = doc.popular_heading
    doc.popular_heading = "What everyone is buying"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    html = _home()
    print("  new wording shows   :", "What everyone is buying" in html)
    print("  old wording gone    :", "Popular right now" not in html)

    print()
    print("=== clearing it restores the original ===")
    doc = frappe.get_single("Website Text")
    doc.popular_heading = ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    html = _home()
    print("  original back       :", "Popular right now" in html)

    # Leave it as it was.
    doc = frappe.get_single("Website Text")
    doc.popular_heading = was
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
