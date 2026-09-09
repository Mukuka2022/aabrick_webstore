"""Reconcile ERPNext warehouses and cost centres with the AABrick operational
branch list (supplied 2026-09-08).

    bench --site www.aabrick.com execute aabrick_webstore.reconcile.preview
    bench --site www.aabrick.com execute aabrick_webstore.reconcile.apply_all
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"

CREATE = {
    "SOS": "Lusaka Province",
    "Chalala": "Lusaka Province",
    "Silverest": "Lusaka Province",
    "Meanwood": "Lusaka Province",
    "Lusaka Great North": "Lusaka Province",
    "Luwingu": "Northern Province",
    "Samfya": "Luapula Province",
    "Livingstone": "Southern Province",
}

RENAMES = [
    ("Ndola - ALZ", "Ndola - AZL", "Ndola 2"),
    ("Mungwi - ALZ", "Mungwi - AZL", "Head Office"),
]

DROP_FIRST = ["Head Office - AZL"]

DELETE = ["Chama", "Isoka", "Kabompo", "Kasempa", "Lilayi", "Lusaka Main",
          "Manna Mall", "Mpongwe", "Mumbwa", "Mwinilunga", "Sesheke", "Zamtan"]

DISABLE = ["Kitwe Pende", "Lufwanyama"]


def _wh(base):
    for cand in ("%s - %s" % (base, ABBR), "%s - ALZ" % base):
        if frappe.db.exists("Warehouse", cand):
            return cand
    return None


def _cc(base):
    full = "%s - %s" % (base, ABBR)
    return full if frappe.db.exists("Cost Center", full) else None


def _plan():
    plan = {"create": [], "rename": [], "drop_first": [],
            "delete": [], "disable": [], "pos": []}

    for base, province in CREATE.items():
        plan["create"].append((base, province,
                               _wh(base) is not None, _cc(base) is not None))

    for wh, cc, new in RENAMES:
        plan["rename"].append((wh, cc, new,
                               bool(frappe.db.exists("Warehouse", wh)),
                               bool(frappe.db.exists("Cost Center", cc))))

    for cc in DROP_FIRST:
        plan["drop_first"].append((cc, bool(frappe.db.exists("Cost Center", cc))))

    for base in DELETE:
        web = "%s Web - %s" % (base, ABBR)
        plan["delete"].append((base, _wh(base), _cc(base),
                               web if frappe.db.exists("Warehouse", web) else None))

    for base in DISABLE:
        plan["disable"].append((base, _wh(base), _cc(base)))

    closing_whs = set()
    for base in DISABLE + DELETE:
        w = _wh(base)
        if w:
            closing_whs.add(w)
    for p in frappe.get_all("POS Profile", fields=["name", "warehouse"]):
        if p.warehouse in closing_whs:
            plan["pos"].append((p.name, p.warehouse))
    return plan


def preview():
    p = _plan()
    print("=" * 72)
    print("BRANCH RECONCILIATION - PREVIEW")
    print("=" * 72)

    print("\n### CREATE (%d)" % len(p["create"]))
    for base, prov, has_wh, has_cc in p["create"]:
        print("   + %-22s under %-22s wh_exists=%s cc_exists=%s"
              % (base, prov, has_wh, has_cc))

    print("\n### DROP FIRST (frees the name for a rename)")
    for cc, exists in p["drop_first"]:
        print("   x %-28s exists=%s" % (cc, exists))

    print("\n### RENAME (%d)" % len(p["rename"]))
    for wh, cc, new, whx, ccx in p["rename"]:
        print("   ~ %-22s -> %-16s (wh=%s cc=%s)" % (wh, new, whx, ccx))

    print("\n### DELETE (%d clean branches)" % len(p["delete"]))
    for base, wh, cc, web in p["delete"]:
        print("   - %-16s wh=%-22s cc=%-18s web=%s" % (base, wh, cc, web))

    print("\n### DISABLE (%d, carry stock or txns)" % len(p["disable"]))
    for base, wh, cc in p["disable"]:
        print("   ! %-16s wh=%-22s cc=%s" % (base, wh, cc))

    print("\n### POS PROFILES affected (%d)" % len(p["pos"]))
    for name, wh in p["pos"]:
        print("   ! %-12s -> %s" % (name, wh))
    return {k: len(v) for k, v in p.items()}


def apply_all():
    p = _plan()
    done = {"dropped": 0, "renamed": 0, "pos_disabled": 0,
            "web_deleted": 0, "deleted": 0, "disabled": 0, "created": 0}
    errors = []

    for cc, exists in p["drop_first"]:
        if exists:
            try:
                frappe.delete_doc("Cost Center", cc, force=1, ignore_permissions=True)
                done["dropped"] += 1
            except Exception as e:
                errors.append(("drop", cc, str(e)[:90]))

    for wh, cc, new, whx, ccx in p["rename"]:
        if whx:
            try:
                frappe.rename_doc("Warehouse", wh, "%s - %s" % (new, ABBR),
                                  force=True)
                done["renamed"] += 1
            except Exception as e:
                errors.append(("rename-wh", wh, str(e)[:90]))
        if ccx:
            try:
                frappe.rename_doc("Cost Center", cc, "%s - %s" % (new, ABBR),
                                  force=True)
            except Exception as e:
                errors.append(("rename-cc", cc, str(e)[:90]))

    for name, wh in p["pos"]:
        try:
            frappe.db.set_value("POS Profile", name, "disabled", 1)
            done["pos_disabled"] += 1
        except Exception as e:
            errors.append(("pos", name, str(e)[:90]))

    for base, wh, cc, web in p["delete"]:
        if web:
            try:
                frappe.delete_doc("Warehouse", web, force=1, ignore_permissions=True)
                done["web_deleted"] += 1
            except Exception as e:
                errors.append(("delete-web", web, str(e)[:90]))
        if wh:
            try:
                frappe.delete_doc("Warehouse", wh, force=1, ignore_permissions=True)
                done["deleted"] += 1
            except Exception as e:
                errors.append(("delete-wh", wh, str(e)[:90]))
        if cc:
            try:
                frappe.delete_doc("Cost Center", cc, force=1, ignore_permissions=True)
            except Exception as e:
                errors.append(("delete-cc", cc, str(e)[:90]))

    for base, wh, cc in p["disable"]:
        if wh:
            try:
                frappe.db.set_value("Warehouse", wh, "disabled", 1)
                done["disabled"] += 1
            except Exception as e:
                errors.append(("disable-wh", wh, str(e)[:90]))
        if cc:
            try:
                frappe.db.set_value("Cost Center", cc, "disabled", 1)
            except Exception as e:
                errors.append(("disable-cc", cc, str(e)[:90]))

    for base, province, has_wh, has_cc in p["create"]:
        if not has_wh:
            try:
                frappe.get_doc({
                    "doctype": "Warehouse", "warehouse_name": base,
                    "parent_warehouse": "%s - %s" % (province, ABBR),
                    "company": COMPANY, "is_group": 0,
                }).insert(ignore_permissions=True)
                done["created"] += 1
            except Exception as e:
                errors.append(("create-wh", base, str(e)[:90]))
        if not has_cc:
            try:
                frappe.get_doc({
                    "doctype": "Cost Center", "cost_center_name": base,
                    "parent_cost_center": "%s - %s" % (province, ABBR),
                    "company": COMPANY, "is_group": 0,
                }).insert(ignore_permissions=True)
            except Exception as e:
                errors.append(("create-cc", base, str(e)[:90]))

    frappe.db.commit()
    print("=" * 72)
    for k, v in done.items():
        print("%-16s : %d" % (k, v))
    print("errors           : %d" % len(errors))
    for kind, target, err in errors[:15]:
        print("  FAIL %-14s %-26s %s" % (kind, target, err))
    print("\nactive leaf warehouses : %d"
          % frappe.db.count("Warehouse", {"is_group": 0, "disabled": 0}))
    print("active leaf cost centres: %d"
          % frappe.db.count("Cost Center", {"is_group": 0, "disabled": 0}))
    return done


def do_renames():
    """Re-run only the renames (they failed on a bad kwarg the first time)."""
    done, errors = 0, []
    for wh, cc, new in RENAMES:
        target_wh = "%s - %s" % (new, ABBR)
        target_cc = "%s - %s" % (new, ABBR)
        if frappe.db.exists("Warehouse", wh):
            try:
                frappe.rename_doc("Warehouse", wh, target_wh, force=True)
                done += 1
                print("warehouse   %-22s -> %s" % (wh, target_wh))
            except Exception as e:
                errors.append(("wh", wh, str(e)[:110]))
        if frappe.db.exists("Cost Center", cc):
            try:
                frappe.rename_doc("Cost Center", cc, target_cc, force=True)
                done += 1
                print("cost centre %-22s -> %s" % (cc, target_cc))
            except Exception as e:
                errors.append(("cc", cc, str(e)[:110]))
    frappe.db.commit()
    print("\nrenamed: %d   errors: %d" % (done, len(errors)))
    for kind, target, err in errors:
        print("  FAIL %-4s %-24s %s" % (kind, target, err))
    return done
