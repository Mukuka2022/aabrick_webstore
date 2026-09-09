"""Restructure the cost centre tree: separate branch trading from central
overheads, and split HQ into a trading shop plus a group-overhead bucket.

    bench --site www.aabrick.com execute aabrick_webstore.restructure.preview
    bench --site www.aabrick.com execute aabrick_webstore.restructure.apply_all
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"
ROOT = "AABrick Zambia Limited - AZL"

BRANCH_OPS = "Branch Operations - AZL"
OVERHEADS = "Central Overheads - AZL"

NEW_GROUPS = [("Branch Operations", ROOT), ("Central Overheads", ROOT)]
MOVE_UNDER_BRANCH_OPS = ["Northern Region - AZL", "Southern Region - AZL"]

# HQ split: the existing 'Head Office' cost centre is really the shop
CC_RENAME = ("Head Office - AZL", "Mungwi Shop - AZL")
WH_RENAME = ("Head Office - AZL", "Mungwi - AZL")

OVERHEAD_CENTRES = ["Head Office", "Finance & IT", "Marketing", "Distribution"]


def preview():
    print("=" * 68)
    print("COST CENTRE RESTRUCTURE - PREVIEW")
    print("=" * 68)

    print("\n### NEW GROUPS")
    for name, parent in NEW_GROUPS:
        full = "%s - %s" % (name, ABBR)
        print("   + %-26s under %-28s exists=%s"
              % (full, parent, bool(frappe.db.exists("Cost Center", full))))

    print("\n### REPARENT")
    for cc in MOVE_UNDER_BRANCH_OPS:
        cur = frappe.db.get_value("Cost Center", cc, "parent_cost_center")
        print("   ~ %-26s %s -> %s" % (cc, cur, BRANCH_OPS))

    print("\n### HQ SPLIT")
    old_cc, new_cc = CC_RENAME
    old_wh, new_wh = WH_RENAME
    print("   ~ cost centre %-22s -> %-22s (exists=%s)"
          % (old_cc, new_cc, bool(frappe.db.exists("Cost Center", old_cc))))
    print("     current parent: %s"
          % frappe.db.get_value("Cost Center", old_cc, "parent_cost_center"))
    print("   ~ warehouse   %-22s -> %-22s (exists=%s)"
          % (old_wh, new_wh, bool(frappe.db.exists("Warehouse", old_wh))))

    print("\n### OVERHEAD COST CENTRES")
    for name in OVERHEAD_CENTRES:
        full = "%s - %s" % (name, ABBR)
        print("   + %-26s under %-28s exists=%s"
              % (full, OVERHEADS, bool(frappe.db.exists("Cost Center", full))))

    print("\n### LEFT ALONE")
    for cc in ("Main - AZL", "Online - AZL"):
        if frappe.db.exists("Cost Center", cc):
            print("   = %-26s parent=%s"
                  % (cc, frappe.db.get_value("Cost Center", cc, "parent_cost_center")))
    return True


def apply_all():
    done = {"groups": 0, "moved": 0, "renamed": 0, "overheads": 0}
    errors = []

    # 1. group layers
    for name, parent in NEW_GROUPS:
        full = "%s - %s" % (name, ABBR)
        if frappe.db.exists("Cost Center", full):
            continue
        try:
            frappe.get_doc({
                "doctype": "Cost Center", "cost_center_name": name,
                "parent_cost_center": parent, "is_group": 1,
                "company": COMPANY,
            }).insert(ignore_permissions=True)
            done["groups"] += 1
        except Exception as e:
            errors.append(("group", full, str(e)[:100]))

    # 2. move the regions under Branch Operations
    for cc in MOVE_UNDER_BRANCH_OPS:
        try:
            doc = frappe.get_doc("Cost Center", cc)
            doc.parent_cost_center = BRANCH_OPS
            doc.save(ignore_permissions=True)
            done["moved"] += 1
        except Exception as e:
            errors.append(("move", cc, str(e)[:100]))

    # 3. HQ split - rename the existing centre to the shop, free the HO name
    old_cc, new_cc = CC_RENAME
    if frappe.db.exists("Cost Center", old_cc) and not frappe.db.exists("Cost Center", new_cc):
        try:
            frappe.rename_doc("Cost Center", old_cc, new_cc, force=True)
            done["renamed"] += 1
        except Exception as e:
            errors.append(("rename-cc", old_cc, str(e)[:100]))

    old_wh, new_wh = WH_RENAME
    if frappe.db.exists("Warehouse", old_wh) and not frappe.db.exists("Warehouse", new_wh):
        try:
            frappe.rename_doc("Warehouse", old_wh, new_wh, force=True)
            done["renamed"] += 1
        except Exception as e:
            errors.append(("rename-wh", old_wh, str(e)[:100]))

    # 4. overhead centres
    for name in OVERHEAD_CENTRES:
        full = "%s - %s" % (name, ABBR)
        if frappe.db.exists("Cost Center", full):
            continue
        try:
            frappe.get_doc({
                "doctype": "Cost Center", "cost_center_name": name,
                "parent_cost_center": OVERHEADS, "is_group": 0,
                "company": COMPANY,
            }).insert(ignore_permissions=True)
            done["overheads"] += 1
        except Exception as e:
            errors.append(("overhead", full, str(e)[:100]))

    frappe.db.commit()
    print("=" * 68)
    for k, v in done.items():
        print("%-10s : %d" % (k, v))
    print("errors     : %d" % len(errors))
    for kind, target, err in errors[:12]:
        print("  FAIL %-12s %-26s %s" % (kind, target, err))
    return done


def show_tree():
    def walk(parent, depth=0):
        kids = frappe.get_all(
            "Cost Center",
            filters={"parent_cost_center": parent},
            fields=["name", "is_group", "disabled"],
            order_by="is_group desc, name",
        )
        for k in kids:
            if k.is_group:
                print("%s%s/" % ("  " * depth, k.name))
                walk(k.name, depth + 1)
            else:
                n = frappe.db.count("Cost Center", {"parent_cost_center": parent})
                tag = "  [disabled]" if k.disabled else ""
                print("%s%s%s" % ("  " * depth, k.name, tag))
    print(ROOT + "/")
    walk(ROOT, 1)
