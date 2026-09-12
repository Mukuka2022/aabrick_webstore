"""The permissions a customer needs to use the cart, and the cost fields
they must not see on the way.

Adding to cart failed for every signed-in customer with a bare
PermissionError. ERPNext's get_item_details calls item.check_permission()
and get_party_account checks the debtors account, so the cart needs a
customer who can read an Item and reach an Account. Item's permissions
were rebuilt for the branch roles during the ERP work, and a Custom
DocPerm replaces the shipped set outright, so the Customer role went with
it. Webshop ships no permissions of its own, so nothing put it back.

Two grants, no wider than they have to be:

  Item     read     get_item_details asks for read and takes nothing else
  Account  select   ERPNext's own check accepts select where that is all a
                    role has. It lets an account be reached through a link
                    field; it does not open the ledger.

Read on Item is the awkward one, because every field on Item sits at
permlevel 0, cost included. So valuation_rate and last_purchase_rate move
up a level, and every role that can read an Item today is given that level
as well. Staff see exactly what they saw before. A customer, holding only
level 0, sees the tile and not what it cost us.

    bench --site SITE execute aabrick_webstore.shop_permissions.run

Safe to run twice.
"""

import frappe
from frappe.permissions import (
    add_permission,
    update_permission_property,
)

# Fields a customer has no business reading, and the level they move to.
COST_FIELDS = ("valuation_rate", "last_purchase_rate")
COST_LEVEL = 1


def _roles_that_read_item():
    """Every role allowed to read an Item right now.

    Read from the meta rather than listed here, so a role added to Item
    after this was written is carried along instead of quietly losing
    sight of cost.
    """
    meta = frappe.get_meta("Item")
    return sorted({
        p.role for p in meta.permissions
        if p.read and p.permlevel == 0 and p.role != "Customer"
    })


def _lift_cost_fields():
    changed = []
    for fieldname in COST_FIELDS:
        current = frappe.db.get_value(
            "Property Setter",
            {"doc_type": "Item", "field_name": fieldname,
             "property": "permlevel"},
            "value",
        )
        if str(current) == str(COST_LEVEL):
            continue
        frappe.make_property_setter({
            "doctype": "Item",
            "fieldname": fieldname,
            "property": "permlevel",
            "value": COST_LEVEL,
            "property_type": "Int",
        }, is_system_generated=False)
        changed.append(fieldname)
    return changed


def run():
    print("=== the two grants ===")

    # Item: plain read at level 0.
    add_permission("Item", "Customer", 0)
    update_permission_property("Item", "Customer", 0, "read", 1)
    print("  Item     Customer read")

    # Account: select only. add_permission gives read, so take it off again
    # and leave the narrow one behind.
    add_permission("Account", "Customer", 0)
    update_permission_property("Account", "Customer", 0, "read", 0)
    update_permission_property("Account", "Customer", 0, "select", 1)
    print("  Account  Customer select, not read")

    print()
    print("=== moving cost out of a customer's reach ===")
    moved = _lift_cost_fields()
    for f in moved:
        print("  %s -> permlevel %d" % (f, COST_LEVEL))
    if not moved:
        print("  already at permlevel %d" % COST_LEVEL)

    print()
    print("=== keeping staff where they were ===")
    for role in _roles_that_read_item():
        add_permission("Item", role, COST_LEVEL)
        update_permission_property("Item", role, COST_LEVEL, "read", 1)
        print("  %-28s level %d read" % (role, COST_LEVEL))

    frappe.db.commit()
    frappe.clear_cache()
    print()
    print("  done. Customer holds level 0 only, so cost is out of reach.")


def check():
    """Report what a customer can and cannot reach. Changes nothing.

    Everything here goes through frappe.get_list, which is what the REST
    API uses. frappe.get_all is get_list with ignore_permissions=True and
    would answer the same whatever the permissions said.
    """
    user = frappe.db.get_value(
        "User", {"user_type": "Website User", "enabled": 1}, "name")
    if not user:
        print("  no website user to check with")
        return

    costly = frappe.db.sql(
        """
        SELECT item_code, valuation_rate FROM `tabItem`
        WHERE IFNULL(valuation_rate, 0) > 0 LIMIT 1
        """,
        as_dict=True,
    )

    frappe.set_user(user)
    print("  checking as", user)
    print("  Item read           :", frappe.has_permission("Item", "read"))
    print("  Account read        :", frappe.has_permission("Account", "read"),
          "(should be False)")
    print("  Account select only :", frappe.only_has_select_perm("Account"))
    print("  permlevels they hold:",
          frappe.get_meta("Item").get_permlevel_access("read"))

    if costly:
        code = costly[0].item_code
        rows = frappe.get_list(
            "Item", filters={"item_code": code},
            fields=["item_code", "item_name", "valuation_rate"])
        got = dict(rows[0]) if rows else {}
        print("  can list an item    :", bool(rows))
        print("  cost came back      :",
              "YES, WRONG" if got.get("valuation_rate") else "no")

    frappe.set_user("Administrator")


def check_staff(user=None):
    """And the other half: staff still see what they saw."""
    if not user:
        user = frappe.db.get_value(
            "Has Role", {"role": "Stock Manager", "parenttype": "User"}, "parent")
    if not user:
        print("  no Stock Manager to check with")
        return

    costly = frappe.db.sql(
        """
        SELECT item_code, valuation_rate FROM `tabItem`
        WHERE IFNULL(valuation_rate, 0) > 0 LIMIT 1
        """,
        as_dict=True,
    )
    if not costly:
        print("  no item with a cost to check")
        return

    frappe.set_user(user)
    print("  checking as", user)
    print("  permlevels they hold:",
          frappe.get_meta("Item").get_permlevel_access("read"))
    rows = frappe.get_list(
        "Item", filters={"item_code": costly[0].item_code},
        fields=["item_code", "valuation_rate"])
    got = dict(rows[0]) if rows else {}
    print("  cost still visible  :",
          "yes" if got.get("valuation_rate") else "NO, THEY LOST IT")
    frappe.set_user("Administrator")
