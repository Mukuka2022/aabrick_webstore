"""One quotation format, and it is one that prints the letter head.

Quotation had seven formats. Three of them, aab3, aa2 and aab2, hold no
content at all and render exactly as ERPNext's Standard does. Two more,
AABrick QUOTE and AC Munda, are the same format saved twice under two
names, one of them a company this is not.

The four with content are Print Format Builder beta formats, and that
matters more than the duplication. A beta format draws its own header out
of format_data and never looks at the Letter Head doctype. Their headers
hold this, in full:

    <div class="document-header"><h3>Quotation</h3><p>{{ doc.name }}</p></div>

No logo, no company name, no TPIN, no address. A quotation printed on one
of them carries nothing that says who sent it, and no letter head can fix
that from the outside, which is the whole reason AC Munda survived on the
paper as long as it did.

So the six are switched off and Quotation prints on Standard, which does
read the Letter Head. Switched off, not deleted: every one of them is a
row that comes straight back.

    bench --site SITE execute aabrick_webstore.print_formats.run

Safe to run twice.

If AABrick want a quotation that looks like more than Standard, the answer
is a custom HTML format, which reads the letter head like Standard does.
A beta format cannot be the answer while the header lives inside it.
"""

import frappe

RETIRE = [
    "AC Munda",        # a different company's name on AABrick's quotation
    "AABrick QUOTE",   # the same format as AC Munda, byte for byte
    "aab quote 2",
    "quotation",
    "aab3",            # no content: Standard under another name
    "aa2",
    "aab2",
]

DEFAULTS = {
    "Quotation": "Standard",
}


def run():
    print("=== switching off the formats that cannot print a letter head ===")
    for name in RETIRE:
        if not frappe.db.exists("Print Format", name):
            print("  %-18s not here" % name)
            continue
        if frappe.db.get_value("Print Format", name, "disabled"):
            print("  %-18s already off" % name)
            continue
        frappe.db.set_value("Print Format", name, "disabled", 1)
        print("  %-18s off" % name)

    print()
    print("=== default format per doctype ===")
    for dt, fmt in DEFAULTS.items():
        frappe.make_property_setter({
            "doctype": dt,
            "doctype_or_field": "DocType",
            "property": "default_print_format",
            "value": fmt,
            "property_type": "Data",
        }, is_system_generated=False)
        print("  %-16s -> %s" % (dt, fmt))

    frappe.db.commit()

    print()
    print("=== what is left enabled for Quotation ===")
    for r in frappe.get_all("Print Format",
                            filters={"doc_type": "Quotation", "disabled": 0},
                            fields=["name", "standard"]):
        print("  %-28s standard=%s" % (r.name, r.standard))
