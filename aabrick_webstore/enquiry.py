"""Website enquiries.

Every "ask about this tile", "send an enquiry" and "ask for a quotation" button
on the site lands here, so an enquiry has to arrive somewhere the sales team
already works. It becomes a Lead, with whatever the customer was looking at
attached: the tile code, the quantity the calculator worked out, the branch
they want to collect from.

The endpoint is open to guests, which is the point, so it is rate limited and
everything written is treated as text rather than markup.
"""

import frappe
from frappe import _
# It is frappe.rate_limiter.rate_limit, not frappe.rate_limit: the second
# does not exist, and referencing it stopped this module importing at all,
# which would have taken the endpoint down with it.
from frappe.rate_limiter import rate_limit

SOURCE = "Website"
MAX_MESSAGE = 2000


def ensure_source():
    """A Lead Source of our own, so website enquiries can be told apart from
    walk-ins in any report."""
    if not frappe.db.exists("Lead Source", SOURCE):
        doc = frappe.get_doc({"doctype": "Lead Source", "source_name": SOURCE})
        doc.flags.ignore_permissions = True
        doc.insert()
        frappe.db.commit()
        return True
    return False


def _clean(value, limit=140):
    """Text, never markup, and never longer than the field can hold."""
    return frappe.utils.strip_html(frappe.as_unicode(value or "")).strip()[:limit]


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=6, seconds=3600, methods=["POST"])
def submit(name=None, phone=None, email=None, branch=None, message=None,
           item_code=None, quantity=None, area=None):
    name = _clean(name)
    phone = _clean(phone, 40)
    email = _clean(email, 140)
    branch = _clean(branch, 140)
    message = _clean(message, MAX_MESSAGE)
    item_code = _clean(item_code, 60)

    if not name or not phone:
        frappe.throw(_("Please give us your name and a phone number."))

    lead = frappe.new_doc("Lead")
    lead.lead_name = name
    lead.mobile_no = phone
    lead.status = "Lead"
    lead.request_type = "Product Enquiry"
    if email:
        lead.email_id = email
    if frappe.db.exists("Lead Source", SOURCE):
        lead.source = SOURCE

    lead.set("notes", [])
    lead.append("notes", {"note": _note(message, branch, item_code, quantity, area)})

    lead.flags.ignore_permissions = True
    lead.insert()
    frappe.db.commit()

    return {"ok": True, "reference": lead.name}


def _note(message, branch, item_code, quantity, area):
    """Everything the customer was looking at, in one readable block, so
    whoever picks the lead up does not have to ask what it is about."""
    lines = []
    if message:
        lines.append(message)
        lines.append("")
    if item_code:
        route = frappe.db.get_value("Website Item", {"item_code": item_code}, "route")
        lines.append("Product: %s" % item_code)
        if route:
            lines.append("Page: %s" % frappe.utils.get_url(route))
    if quantity:
        lines.append("Quantity worked out: %s" % _clean(quantity, 40))
    if area:
        lines.append("Area: %s" % _clean(area, 40))
    if branch:
        lines.append("Preferred branch: %s" % branch)
    lines.append("Sent from the website")
    return "\n".join(lines)
