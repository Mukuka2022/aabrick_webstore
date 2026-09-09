"""Structural cleanup while the system is still unused.

  1. Warehouses carrying the old ALZ abbreviation get renamed to AZL
  2. Orphaned warehouses (null parent) re-parented
  3. Item Price rows with a UOM the item does not have
  4. Legacy 5200 expense accounts superseded by the new branch/central groups

    bench --site www.aabrick.com execute aabrick_webstore.cleanup.preview
    bench --site www.aabrick.com execute aabrick_webstore.cleanup.apply_all
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"
ALL_WAREHOUSES = "All Warehouses - AZL"

# superseded by 5300 Branch Operating / 5400 Distribution / 5500 Central Overheads
LEGACY_TO_DISABLE = [
    "5201 - Administrative Expenses - AZL",
    "5204 - Entertainment Expenses - AZL",
    "5208 - Office Maintenance Expenses - AZL",
    "5209 - Office Rent - AZL",
    "5210 - Postal Expenses - AZL",
    "5211 - Print and Stationery - AZL",
    "5213 - Salary - AZL",
    "5215 - Telephone Expenses - AZL",
    "5216 - Travel Expenses - AZL",
    "5217 - Utility Expenses - AZL",
]


def _alz_warehouses():
    return sorted(frappe.get_all(
        "Warehouse", filters={"name": ["like", "%- ALZ"]}, pluck="name"))


def _orphans():
    rows = frappe.get_all("Warehouse",
                          filters={"company": COMPANY},
                          fields=["name", "parent_warehouse", "is_group"])
    return [r for r in rows
            if not r.parent_warehouse and r.name != ALL_WAREHOUSES]


def _bad_uom_prices():
    return frappe.db.sql("""
        SELECT ip.name, ip.item_code, ip.price_list, ip.uom,
               i.stock_uom, ip.price_list_rate
        FROM `tabItem Price` ip
        JOIN `tabItem` i ON i.name = ip.item_code
        WHERE IFNULL(ip.uom,'') <> ''
          AND ip.uom <> i.stock_uom
          AND NOT EXISTS (SELECT 1 FROM `tabUOM Conversion Detail` ucd
                          WHERE ucd.parent = i.name AND ucd.uom = ip.uom)
    """, as_dict=True)


def preview():
    alz = _alz_warehouses()
    print("=" * 68)
    print("CLEANUP PREVIEW")
    print("=" * 68)

    print("\n1. WAREHOUSES WITH THE OLD ALZ ABBREVIATION (%d)" % len(alz))
    for w in alz[:8]:
        print("   ~ %-28s -> %s" % (w, w[:-len(" - ALZ")] + " - " + ABBR))
    print("   ... %d more" % max(0, len(alz) - 8))

    orphans = _orphans()
    print("\n2. ORPHANED WAREHOUSES (%d)" % len(orphans))
    for o in orphans:
        print("   ~ %-28s is_group=%s -> under %s"
              % (o.name, o.is_group, ALL_WAREHOUSES))

    bad = _bad_uom_prices()
    print("\n3. ITEM PRICES WITH AN INVALID UOM (%d)" % len(bad))
    for r in bad:
        print("   ~ %-12s %-17s uom=%-6s stock_uom=%-5s rate=%.2f"
              % (r.item_code, r.price_list, r.uom, r.stock_uom, r.price_list_rate))
    print("   -> uom cleared so the price applies to the stock UOM")

    print("\n4. LEGACY EXPENSE ACCOUNTS TO DISABLE (%d)" % len(LEGACY_TO_DISABLE))
    for a in LEGACY_TO_DISABLE:
        exists = frappe.db.exists("Account", a)
        used = frappe.db.count("GL Entry", {"account": a}) if exists else 0
        print("   ~ %-46s exists=%s gl_entries=%d" % (a, bool(exists), used))
    return {"alz": len(alz), "orphans": len(orphans), "bad_uom": len(bad)}


def apply_all():
    done = {"renamed": 0, "reparented": 0, "uom_fixed": 0, "disabled": 0}
    errors = []

    # 1. rename ALZ -> AZL
    for old in _alz_warehouses():
        new = old[: -len(" - ALZ")] + " - " + ABBR
        if frappe.db.exists("Warehouse", new):
            errors.append(("rename", old, "target %s already exists" % new))
            continue
        try:
            frappe.rename_doc("Warehouse", old, new, force=True)
            done["renamed"] += 1
        except Exception as e:
            errors.append(("rename", old, str(e)[:100]))
    frappe.db.commit()

    # 2. re-parent orphans
    for o in _orphans():
        try:
            doc = frappe.get_doc("Warehouse", o.name)
            doc.parent_warehouse = ALL_WAREHOUSES
            doc.save(ignore_permissions=True)
            done["reparented"] += 1
        except Exception as e:
            errors.append(("reparent", o.name, str(e)[:100]))
    frappe.db.commit()

    # 3. clear invalid UOMs on price rows
    for r in _bad_uom_prices():
        try:
            frappe.db.set_value("Item Price", r.name, "uom", None)
            done["uom_fixed"] += 1
        except Exception as e:
            errors.append(("uom", r.item_code, str(e)[:100]))
    frappe.db.commit()

    # 4. disable superseded legacy accounts that carry no history
    for a in LEGACY_TO_DISABLE:
        if not frappe.db.exists("Account", a):
            continue
        if frappe.db.count("GL Entry", {"account": a}):
            errors.append(("disable", a, "has GL entries - left enabled"))
            continue
        try:
            frappe.db.set_value("Account", a, "disabled", 1)
            done["disabled"] += 1
        except Exception as e:
            errors.append(("disable", a, str(e)[:100]))
    frappe.db.commit()
    frappe.clear_cache()

    print("=" * 68)
    for k, v in done.items():
        print("%-12s : %d" % (k, v))
    print("errors       : %d" % len(errors))
    for kind, target, err in errors[:15]:
        print("   %-10s %-30s %s" % (kind, target, err))

    print("\nremaining ALZ warehouses : %d" % len(_alz_warehouses()))
    print("remaining orphans        : %d" % len(_orphans()))
    print("remaining bad UOM prices : %d" % len(_bad_uom_prices()))
    return done
