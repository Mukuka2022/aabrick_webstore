"""One letter head for every document AABrick prints.

Three things were wrong, and the first one is the reason this exists.

The letter head marked default was AC Munda Zambia Limited, which is not
this company. Company.default_letter_head was empty, so ERPNext fell back
to the default, and a fresh Quotation came out stamped AC Munda. Forty
quotations and five sales orders already carry it.

The AABrick letter head that did exist was a logo and nothing else, with a
footer holding a website address inside a half empty table. Nothing on it
said who the company is, where it is, or what its TPIN is, and a Zambian
tax invoice has to say the last of those.

So the letter head is built here, from DETAILS below, and set as the
company default so every doctype picks it up: Quotation, Sales Invoice,
Delivery Note, Sales Order, Payment Entry, Purchase Order, all of them.

    bench --site SITE execute aabrick_webstore.letterhead.run

Safe to run twice. Run it again after changing anything in DETAILS.

A blank in DETAILS is left out of the printed page rather than printed as
a placeholder, so this is safe to install before every value is known. The
TPIN is the one to fill in first.
"""

import frappe

NAME = "AABrick Zambia Limited"

# The only place to edit. Everything printed is built from this.
DETAILS = {
    "legal_name": "AABrick Zambia Limited",
    "logo": "/files/AAbrick-logo.png",
    # Blank until AABrick supplies them. Each is dropped when empty.
    "tpin": "",
    "vat": "",
    "address": "",
    "email": "",
    # Known from the website.
    "phone": "+260 960 787 777",
    "website": "www.aabrick.com",
    "strap": "46 branches nationwide",
}

RED = "#B90000"
INK = "#202020"
MUTED = "#5F5F5F"
RULE = "#DCDCDC"


def _details():
    """DETAILS, with the TPIN taken from the Company record when it is set.

    Somebody filling in the tax ID on the Company is doing the obvious
    thing, and the letter head should follow it rather than disagree with
    it in print.
    """
    d = dict(DETAILS)
    tax_id = frappe.db.get_value("Company", NAME, "tax_id")
    if tax_id and not d["tpin"]:
        d["tpin"] = tax_id
    return d


def header_html(d=None):
    d = d or _details()

    right = []
    if d["legal_name"]:
        right.append('<strong style="color:%s">%s</strong>' % (INK, d["legal_name"]))
    if d["tpin"]:
        right.append("TPIN %s" % d["tpin"])
    if d["vat"]:
        right.append("VAT %s" % d["vat"])
    if d["phone"]:
        right.append(d["phone"])
    if d["website"]:
        right.append(d["website"])

    return (
        '<table style="width:100%%;border-collapse:collapse;border:0">'
        '<tr>'
        '<td style="width:55%%;vertical-align:middle;border:0;padding:0">'
        '<img src="%s" alt="%s" style="height:58px">'
        '</td>'
        '<td style="width:45%%;vertical-align:middle;border:0;padding:0;'
        'text-align:right;font-size:8.5pt;line-height:1.5;color:%s">%s</td>'
        '</tr></table>'
        '<div style="border-bottom:2px solid %s;margin-top:8px"></div>'
        % (d["logo"], d["legal_name"], MUTED, "<br>".join(right), RED)
    )


def footer_html(d=None):
    d = d or _details()

    bits = []
    if d["address"]:
        bits.append(d["address"])
    if d["strap"]:
        bits.append(d["strap"])
    if d["email"]:
        bits.append(d["email"])
    if d["website"]:
        bits.append(d["website"])

    return (
        '<div style="border-top:1px solid %s;padding-top:6px;'
        'font-size:7.5pt;line-height:1.5;color:%s;text-align:center">%s</div>'
        % (RULE, MUTED, " &nbsp;&middot;&nbsp; ".join(bits))
    )


def run():
    d = _details()

    # MariaDB matches a name without regard to case, so looking up
    # "AABrick Zambia Limited" finds the "AABRICK ZAMBIA LIMITED" record
    # that is already there. Take the spelling the database actually holds
    # and use it everywhere, or Company.default_letter_head ends up
    # pointing at a name no record is called.
    existing = frappe.db.get_value("Letter Head", NAME, "name")
    if existing:
        doc = frappe.get_doc("Letter Head", existing)
    else:
        doc = frappe.new_doc("Letter Head")
        doc.letter_head_name = NAME
    doc.source = "HTML"
    doc.content = header_html(d)
    doc.footer = footer_html(d)
    doc.disabled = 0
    doc.is_default = 1
    doc.save(ignore_permissions=True)
    name = doc.name
    print("letter head saved:", name)

    # is_default on this one does not clear the other by itself in every
    # version, and two defaults is how AC Munda got onto the paper.
    for other in frappe.get_all("Letter Head",
                                filters={"is_default": 1,
                                         "name": ["!=", name]},
                                pluck="name"):
        frappe.db.set_value("Letter Head", other, "is_default", 0)
        print("  no longer default:", other)

    frappe.db.set_value("Company", NAME, "default_letter_head", name)
    print("company default letter head:", name)

    frappe.db.commit()

    print()
    missing = [k for k in ("tpin", "address", "email") if not d[k]]
    if missing:
        print("still to supply, and left off the page until they are:")
        for k in missing:
            print("   ", k)
    else:
        print("every detail is filled in")
