"""Build a Cost Center tree mirroring the Warehouse tree, so each branch
can be reported on for profit and loss.

    bench --site www.aabrick.com execute aabrick_webstore.cost_centres.preview
    bench --site www.aabrick.com execute aabrick_webstore.cost_centres.apply_tree
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"
ROOT = "AABrick Zambia Limited - AZL"

# Warehouse groups that are not real places
SKIP_GROUPS = {"All Warehouses - AZL", "Website Warehouses - AZL"}
# ERPNext's default stock buckets - not branches
SKIP_LEAVES = {
    "Stores - AZL", "Finished Goods - AZL", "Goods In Transit - AZL",
    "Rejected Items - AZL", "Work In Progress - AZL", "Website stock - AZL",
}


def clean(warehouse_name):
    """'Mkushi - ALZ - AZL' -> 'Mkushi'   (strips the transposed ALZ typo too)"""
    n = warehouse_name
    for suffix in (" - %s" % ABBR, " - ALZ"):
        while n.endswith(suffix):
            n = n[: -len(suffix)]
    return n.strip()


def _plan():
    """Return ordered list of (cost_center_name, parent_name, is_group)."""
    provinces = frappe.get_all(
        "Warehouse",
        filters={"is_group": 1, "company": COMPANY},
        fields=["name", "parent_warehouse"],
        order_by="name",
    )
    regions, province_rows = {}, []
    for p in provinces:
        if p.name in SKIP_GROUPS:
            continue
        parent = p.parent_warehouse
        if not parent or parent in SKIP_GROUPS:
            # a region sits directly under All Warehouses
            regions[p.name] = True
        else:
            province_rows.append(p)

    plan = []
    for region in sorted(regions):
        plan.append((clean(region), ROOT, 1))
    for p in sorted(province_rows, key=lambda r: r.name):
        plan.append((clean(p.name), clean(p.parent_warehouse) + " - " + ABBR, 1))

    leaves = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0, "company": COMPANY},
        fields=["name", "parent_warehouse"],
        order_by="name",
    )
    for w in leaves:
        if w.name in SKIP_LEAVES or not w.parent_warehouse:
            continue
        if w.parent_warehouse in SKIP_GROUPS:
            continue  # website warehouses roll up to 'Online'
        plan.append((clean(w.name), clean(w.parent_warehouse) + " - " + ABBR, 0))

    plan.append(("Online", ROOT, 0))
    plan.append(("Head Office", ROOT, 0))
    return plan


def _report(plan):
    exists = new = 0
    print("=" * 64)
    print("COST CENTRE PLAN (%d nodes)" % len(plan))
    print("=" * 64)
    for name, parent, is_group in plan:
        full = "%s - %s" % (name, ABBR)
        if frappe.db.exists("Cost Center", full):
            exists += 1
        else:
            new += 1
            kind = "GROUP " if is_group else "branch"
            print("  + %-6s %-28s under %s" % (kind, full, parent))
    print()
    print("to create: %d    already present: %d" % (new, exists))
    return new, exists


def preview():
    plan = _plan()
    return _report(plan)


def apply_tree():
    plan = _plan()
    created = skipped = 0
    errors = []
    for name, parent, is_group in plan:
        full = "%s - %s" % (name, ABBR)
        if frappe.db.exists("Cost Center", full):
            skipped += 1
            continue
        try:
            frappe.get_doc({
                "doctype": "Cost Center",
                "cost_center_name": name,
                "parent_cost_center": parent,
                "is_group": is_group,
                "company": COMPANY,
            }).insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            errors.append((full, parent, str(e)[:100]))
    frappe.db.commit()
    print("=" * 64)
    print("cost centres created : %d" % created)
    print("already present      : %d" % skipped)
    print("errors               : %d" % len(errors))
    for full, parent, err in errors[:12]:
        print("  FAIL %-26s under %-26s %s" % (full, parent, err))
    total = frappe.db.count("Cost Center", {"company": COMPANY})
    print("\ntotal cost centres now: %d" % total)
    return {"created": created, "skipped": skipped, "errors": len(errors)}
