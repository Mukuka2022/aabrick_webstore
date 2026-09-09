"""Clean the user base down to admins, then build the branch role structure
from the AABrick org chart.

    bench --site www.aabrick.com execute aabrick_webstore.roles_setup.preview
    bench --site www.aabrick.com execute aabrick_webstore.roles_setup.apply_all
"""

import frappe
from frappe.permissions import add_permission, update_permission_property

KEEP = {"Administrator", "Guest", "tungati.m@gmail.com"}

# custom roles the org chart needs that ERPNext has no equivalent for
NEW_ROLES = [
    "Branch Supervisor",
    "Branch Cashier",
    "Branch Sales Assistant",
    "Branch Stock Clerk",
    "Area Business Manager",
]

# flag letters -> DocPerm fields
FLAGS = {
    "c": "create", "r": "read", "w": "write", "s": "submit",
    "x": "cancel", "a": "amend", "d": "delete", "p": "print", "e": "export",
}

MATRIX = {
    "Branch Cashier": {
        "POS Invoice":        "crwsp",
        "POS Opening Entry":  "crws",
        "POS Closing Entry":  "crws",
        "POS Profile":        "r",
        "Sales Invoice":      "rp",
        "Customer":           "crw",
        "Item":               "r",
        "Item Price":         "r",
        "Mode of Payment":    "r",
        "Bin":                "r",
    },
    "Branch Sales Assistant": {
        "Quotation":          "crwsp",
        "Sales Order":        "crwsp",
        "Customer":           "crw",
        "Item":               "r",
        "Item Price":         "r",
        "Sales Invoice":      "rp",
        "Delivery Note":      "rp",
        "Bin":                "r",
    },
    "Branch Stock Clerk": {
        "Stock Entry":          "crwsp",
        "Material Request":     "crwsp",
        "Stock Reconciliation": "crw",
        "Purchase Receipt":     "crwp",
        "Delivery Note":        "crwsp",
        "Stock Ledger Entry":   "r",
        "Bin":                  "r",
        "Item":                 "r",
        "Warehouse":            "r",
    },
    "Branch Supervisor": {
        "POS Invoice":          "crwsxap",
        "POS Closing Entry":    "crwsx",
        "Sales Invoice":        "crwsxp",
        "Sales Order":          "crwsxp",
        "Quotation":            "crwsxp",
        "Delivery Note":        "crwsxp",
        "Stock Entry":          "crwsxp",
        "Material Request":     "crwsx",
        "Stock Reconciliation": "crws",
        "Customer":             "crw",
        "Item":                 "r",
        "Item Price":           "r",
        "Bin":                  "r",
        "Warehouse":            "r",
    },
    "Area Business Manager": {
        "Sales Invoice":        "rsxpe",
        "Sales Order":          "rwsxpe",
        "Quotation":            "rwspe",
        "Delivery Note":        "rwsxpe",
        "Stock Entry":          "rspe",
        "Material Request":     "rwspe",
        "Stock Reconciliation": "rspe",
        "POS Invoice":          "rpe",
        "POS Closing Entry":    "rspe",
        "Customer":             "rwe",
        "Item":                 "rwe",
        "Item Price":           "re",
        "Bin":                  "re",
        "Warehouse":            "r",
        "Stock Ledger Entry":   "re",
    },
}


def _targets():
    return frappe.get_all(
        "User",
        filters={"user_type": "System User", "enabled": 1,
                 "name": ["not in", list(KEEP)]},
        fields=["name", "full_name"],
    )


def preview():
    users = _targets()
    print("=" * 70)
    print("USER CLEANUP + ROLE SETUP - PREVIEW")
    print("=" * 70)
    print("\nKEEPING as System User: %s" % ", ".join(sorted(KEEP)))
    print("\nCONVERT to Website User and strip roles: %d users" % len(users))
    for u in users[:10]:
        n = frappe.db.count("Has Role", {"parent": u.name})
        print("   - %-38s %-14s %d roles" % (u.name, u.full_name or "", n))
    print("   ... %d more" % max(0, len(users) - 10))

    total_roles = frappe.db.sql("""SELECT COUNT(*) FROM `tabHas Role`
        WHERE parent NOT IN %(keep)s""", {"keep": tuple(KEEP)})[0][0]
    print("\n   role assignments to be removed: %d" % total_roles)

    print("\nNEW ROLES")
    for r in NEW_ROLES:
        print("   + %-26s exists=%s" % (r, bool(frappe.db.exists("Role", r))))

    print("\nPERMISSION MATRIX")
    for role, perms in MATRIX.items():
        print("   %s" % role)
        for dt, flags in perms.items():
            names = ", ".join(FLAGS[f] for f in flags)
            print("      %-24s %s" % (dt, names))
    return {"convert": len(users), "roles": len(NEW_ROLES)}


def apply_all():
    converted = roles_removed = 0
    errors = []

    # 1. strip roles + demote to Website User
    for u in _targets():
        try:
            n = frappe.db.count("Has Role", {"parent": u.name})
            frappe.db.delete("Has Role", {"parent": u.name})
            roles_removed += n
            frappe.db.set_value("User", u.name, "user_type", "Website User")
            converted += 1
        except Exception as e:
            errors.append(("convert", u.name, str(e)[:90]))

    # 2. custom roles
    made = 0
    for r in NEW_ROLES:
        if frappe.db.exists("Role", r):
            frappe.db.set_value("Role", r, "disabled", 0)
            continue
        try:
            frappe.get_doc({
                "doctype": "Role", "role_name": r,
                "desk_access": 1, "is_custom": 1,
            }).insert(ignore_permissions=True)
            made += 1
        except Exception as e:
            errors.append(("role", r, str(e)[:90]))

    frappe.db.commit()

    # 3. permission matrix
    granted = 0
    for role, perms in MATRIX.items():
        for dt, flags in perms.items():
            if not frappe.db.exists("DocType", dt):
                errors.append(("doctype", dt, "not installed"))
                continue
            try:
                add_permission(dt, role, 0)
                for f in flags:
                    update_permission_property(dt, role, 0, FLAGS[f], 1)
                granted += 1
            except Exception as e:
                errors.append(("perm", "%s/%s" % (role, dt), str(e)[:90]))

    frappe.db.commit()
    frappe.clear_cache()

    print("users converted to Website User : %d" % converted)
    print("role assignments removed        : %d" % roles_removed)
    print("custom roles created            : %d" % made)
    print("doctype permissions granted     : %d" % granted)
    print("errors                          : %d" % len(errors))
    for kind, target, err in errors[:15]:
        print("  FAIL %-10s %-34s %s" % (kind, target, err))

    left = frappe.db.count("User", {"user_type": "System User", "enabled": 1})
    print("\nenabled System Users remaining  : %d" % left)
    for u in frappe.get_all("User", filters={"user_type": "System User", "enabled": 1},
                            pluck="name"):
        print("   %s" % u)
    return {"converted": converted, "granted": granted, "errors": len(errors)}


# junior branch roles must not be able to bulk-export master data
NO_EXPORT_ROLES = ["Branch Cashier", "Branch Sales Assistant", "Branch Stock Clerk"]
# even a supervisor should not export the full price book or customer list
SUPERVISOR_NO_EXPORT_ON = ["Item", "Item Price", "Customer", "Bin", "Warehouse"]


def tighten_export():
    """Frappe's add_permission() sets export=1 by default, which would let a
    cashier download the whole customer list and price book. Revoke it."""
    changed = []
    for role in NO_EXPORT_ROLES:
        rows = frappe.get_all("Custom DocPerm",
                              filters={"role": role, "export": 1},
                              fields=["name", "parent"])
        for r in rows:
            frappe.db.set_value("Custom DocPerm", r.name, "export", 0)
            changed.append((role, r.parent))

    for dt in SUPERVISOR_NO_EXPORT_ON:
        rows = frappe.get_all("Custom DocPerm",
                              filters={"role": "Branch Supervisor",
                                       "parent": dt, "export": 1},
                              fields=["name", "parent"])
        for r in rows:
            frappe.db.set_value("Custom DocPerm", r.name, "export", 0)
            changed.append(("Branch Supervisor", r.parent))

    frappe.db.commit()
    frappe.clear_cache()
    print("export revoked on %d role/doctype pairs" % len(changed))
    for role, dt in changed:
        print("   %-24s %s" % (role, dt))

    print("\nremaining export rights:")
    for role in NO_EXPORT_ROLES + ["Branch Supervisor", "Area Business Manager"]:
        n = frappe.db.count("Custom DocPerm", {"role": role, "export": 1})
        print("   %-24s %d doctypes" % (role, n))
    return len(changed)
