"""Two rules that used to be Server Scripts.

Signing up was failing with "Server Scripts are disabled". Four Server
Script records sit in this database and every one of them throws, because
server_script_enabled has never been set. Two of them matter:

  Signup as Customer on Website   User, After Insert
  Coupon                          Sales Order, Before Insert

The first is why signing up broke. The second would have broken placing an
order in exactly the same way, which nobody had hit yet because ordering
needs an account and accounts could not be made.

They are here as code now rather than enabled where they were. Three
reasons. A Server Script lives in the database, so it does not travel with
a git pull and the live server would need it re-entered by hand. It is
edited in the browser on the live server, which is the thing AABrick has
decided not to do. And turning server scripts on to rescue two of these
would also have woken the other two, which publish every item quantity in
every warehouse to anyone who asks.
"""

import frappe


def user_after_insert(doc, method=None):
    """A customer who signs up on the website is a customer.

    Without the Customer role the portal has nothing in it: orders,
    invoices and addresses are all gated on it.

    owner == Guest is what marks a self registration. A user created by
    staff in the desk is not given the role automatically, because that is
    a decision somebody is making deliberately.
    """
    if doc.user_type != "Website User":
        return
    if doc.owner != "Guest":
        return
    doc.add_roles("Customer")


def sales_order_before_insert(doc, method=None):
    """An order placed with a coupon belongs to whoever the coupon belongs to.

    The sales team is cleared first: the salesperson is being set from the
    coupon, so anything already in there would double the allocation and
    ERPNext refuses a total over one hundred percent.
    """
    if not doc.get("coupon_code"):
        return

    sales_person = frappe.db.get_value(
        "Coupon Code", doc.coupon_code, "sales_person")
    if not sales_person:
        return

    doc.set("sales_team", [])
    doc.append("sales_team", {
        "sales_person": sales_person,
        "allocated_percentage": 100,
    })


def retire_server_scripts():
    """Switch off the four records, now that the two that matter are code.

        bench --site SITE execute \\
            aabrick_webstore.portal_rules.retire_server_scripts

    Safe to run twice. Nothing is deleted: the two stock ones are somebody's
    work and AABrick should look at them before they go for good.
    """
    if not frappe.db.sql("SHOW TABLES LIKE 'tabServer Script'"):
        print("  no Server Script table on this site")
        return

    rows = frappe.db.sql(
        "SELECT name, disabled FROM `tabServer Script`", as_dict=True)
    if not rows:
        print("  no Server Scripts on this site")
        return

    for r in rows:
        if r.disabled:
            print("  %-34s already off" % r.name)
            continue
        frappe.db.set_value("Server Script", r.name, "disabled", 1)
        print("  %-34s switched off" % r.name)

    frappe.db.commit()
    # The map frappe consults on every insert is cached.
    frappe.cache().delete_value("server_script_map")
    frappe.clear_cache()
    print()
    print("  the two that matter are now in aabrick_webstore.portal_rules")
