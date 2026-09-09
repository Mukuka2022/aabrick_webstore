"""Scaffolding ahead of the branch worksheet coming back:

  A. Business Area doctype + accounting dimension + link field on Warehouse
  B. Reconcile the HRMS Branch list with the 46 active branches
  C. One POS Profile per branch, correctly wired to warehouse and cost centre

    bench --site www.aabrick.com execute aabrick_webstore.scaffold.preview
    bench --site www.aabrick.com execute aabrick_webstore.scaffold.build_area_dimension
    bench --site www.aabrick.com execute aabrick_webstore.scaffold.reconcile_hr_branches
    bench --site www.aabrick.com execute aabrick_webstore.scaffold.apply_pos_profiles
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"
MODULE = "Aabrick Webstore"

SKIP_PARENTS = ("All Warehouses - AZL", "Website Warehouses - AZL")

# POS sells at counter prices; the Web Price List is deliberately +10
POS_PRICE_LIST = "Standard Selling"
POS_INCOME = "4110 - Sales - AZL"
POS_WRITE_OFF = "5218 - Write Off - AZL"
POS_PAYMENTS = ["Cash", "Mobile Money"]


def _branches():
    """Active branch warehouses with cleaned name and matching cost centre."""
    out = []
    rows = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0, "disabled": 0, "company": COMPANY},
        fields=["name", "parent_warehouse"],
        order_by="name",
    )
    for r in rows:
        if not r.parent_warehouse or r.parent_warehouse in SKIP_PARENTS:
            continue
        clean = r.name
        for suffix in (" - %s" % ABBR, " - ALZ"):
            while clean.endswith(suffix):
                clean = clean[: -len(suffix)]
        cc = "%s - %s" % (clean, ABBR)
        out.append({
            "branch": clean,
            "warehouse": r.name,
            "cost_center": cc if frappe.db.exists("Cost Center", cc) else None,
            "province": r.parent_warehouse.replace(" - %s" % ABBR, ""),
        })
    return out


# ---------------------------------------------------------------- A
def build_area_dimension():
    """Business Area as an accounting dimension, kept out of the cost centre
    tree so territories can be re-cut without a ledger migration."""
    made = []

    if not frappe.db.exists("DocType", "Business Area"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "Business Area",
            "module": MODULE,
            "custom": 0,
            "autoname": "field:area_name",
            "naming_rule": "By fieldname",
            "track_changes": 1,
            "allow_rename": 1,
            "fields": [
                {"fieldname": "area_name", "label": "Area Name", "fieldtype": "Data",
                 "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "region", "label": "Region", "fieldtype": "Select",
                 "options": "North\nSouth", "reqd": 1, "in_list_view": 1},
                {"fieldname": "area_manager", "label": "Area Business Manager",
                 "fieldtype": "Link", "options": "User", "in_list_view": 1},
                {"fieldname": "company", "label": "Company", "fieldtype": "Link",
                 "options": "Company", "default": COMPANY},
                {"fieldname": "disabled", "label": "Disabled", "fieldtype": "Check"},
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1,
                 "create": 1, "delete": 1},
                {"role": "Accounts Manager", "read": 1, "write": 1, "create": 1},
                {"role": "Area Business Manager", "read": 1},
            ],
        }).insert(ignore_permissions=True)
        made.append("DocType Business Area")

    # link field on Warehouse so a branch knows its area
    if not frappe.db.exists("Custom Field", "Warehouse-business_area"):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Warehouse",
            "fieldname": "business_area",
            "label": "Business Area",
            "fieldtype": "Link",
            "options": "Business Area",
            "insert_after": "parent_warehouse",
        }).insert(ignore_permissions=True)
        made.append("Custom Field Warehouse.business_area")

    frappe.db.commit()

    if not frappe.db.exists("Accounting Dimension", {"document_type": "Business Area"}):
        try:
            frappe.get_doc({
                "doctype": "Accounting Dimension",
                "document_type": "Business Area",
            }).insert(ignore_permissions=True)
            made.append("Accounting Dimension Business Area")
        except Exception as e:
            print("accounting dimension failed: %s" % str(e)[:160])

    frappe.db.commit()
    print("created:")
    for m in made:
        print("   + %s" % m)
    if not made:
        print("   (everything already present)")
    return made


# ---------------------------------------------------------------- B
def reconcile_hr_branches():
    """Add the 46 active branches to the HRMS Branch list. Report stale entries
    but never delete one an employee still points at."""
    active = {b["branch"] for b in _branches()}
    existing = set(frappe.get_all("Branch", pluck="name"))

    created, protected, removable = [], [], []

    for name in sorted(active - existing):
        try:
            frappe.get_doc({"doctype": "Branch",
                            "branch": name}).insert(ignore_permissions=True)
            created.append(name)
        except Exception as e:
            print("   FAIL create %-18s %s" % (name, str(e)[:80]))

    for name in sorted(existing - active):
        n = frappe.db.count("Employee", {"branch": name})
        if n:
            protected.append((name, n))
        else:
            removable.append(name)

    frappe.db.commit()
    print("HR BRANCH RECONCILIATION")
    print("  created (%d): %s" % (len(created), ", ".join(created) or "none"))
    print("\n  stale but IN USE by employees, left alone (%d):" % len(protected))
    for name, n in protected:
        print("     %-20s %d employees" % (name, n))
    print("\n  stale and unused, safe to delete (%d):" % len(removable))
    print("     %s" % (", ".join(removable) or "none"))
    return {"created": len(created), "protected": len(protected),
            "removable": len(removable)}


# ---------------------------------------------------------------- C
def build_pos_profiles(apply=False):
    """One POS Profile per branch, wired to that warehouse and cost centre.
    Cashier assignment is deliberately left empty for the worksheet."""
    rows = _branches()
    created, skipped, errors = 0, 0, []
    missing_cc = []

    payments = [m for m in POS_PAYMENTS if frappe.db.exists("Mode of Payment", m)]

    for b in rows:
        name = "%s POS" % b["branch"]
        if frappe.db.exists("POS Profile", name):
            skipped += 1
            continue
        if not b["cost_center"]:
            missing_cc.append(b["branch"])
            continue
        if not apply:
            created += 1
            continue
        try:
            frappe.get_doc({
                "doctype": "POS Profile",
                "name": name,
                "company": COMPANY,
                "warehouse": b["warehouse"],
                "cost_center": b["cost_center"],
                "write_off_cost_center": b["cost_center"],
                "income_account": POS_INCOME,
                "write_off_account": POS_WRITE_OFF,
                "selling_price_list": POS_PRICE_LIST,
                "currency": "ZMW",
                "disabled": 0,
                "payments": [
                    {"mode_of_payment": m, "default": 1 if i == 0 else 0}
                    for i, m in enumerate(payments)
                ],
            }).insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            errors.append((name, str(e)[:110]))

    if apply:
        frappe.db.commit()
    print("=" * 64)
    print("POS PROFILES - %s" % ("APPLIED" if apply else "PREVIEW"))
    print("=" * 64)
    print("branches            : %d" % len(rows))
    print("profiles created    : %d" % created)
    print("already present     : %d" % skipped)
    print("no cost centre      : %s" % (", ".join(missing_cc) or "none"))
    print("payment modes       : %s" % ", ".join(payments))
    print("errors              : %d" % len(errors))
    for name, err in errors[:12]:
        print("   FAIL %-24s %s" % (name, err))
    print("\nprice list on every profile: %s" % POS_PRICE_LIST)
    return {"created": created, "errors": len(errors)}


def apply_pos_profiles():
    return build_pos_profiles(apply=True)


def preview():
    rows = _branches()
    print("branches found: %d" % len(rows))
    for b in rows[:6]:
        print("   %-20s wh=%-24s cc=%s"
              % (b["branch"], b["warehouse"], b["cost_center"]))
    print("   ...")
    return len(rows)


# a branch reconciles each wallet separately, so each gets its own mode
MODE_ACCOUNTS = {
    "Cash": "1110 - Cash - AZL",
    "Airtel Money": None,   # resolved by lookup below
    "MTN MoMo": None,
}

# warehouse name -> cost centre where they deliberately differ
COST_CENTRE_OVERRIDES = {
    "Mungwi": "Mungwi Shop - AZL",
}


def setup_payment_modes():
    """POS Profiles cannot save until every Mode of Payment has a default
    account for the company."""
    airtel = frappe.db.get_value("Account",
                                 {"account_name": ["like", "Airtel%"],
                                  "company": COMPANY, "is_group": 0}, "name")
    mtn = frappe.db.get_value("Account",
                              {"account_name": ["like", "MTN%"],
                               "company": COMPANY, "is_group": 0}, "name")
    MODE_ACCOUNTS["Airtel Money"] = airtel
    MODE_ACCOUNTS["MTN MoMo"] = mtn

    done = []
    for mode, account in MODE_ACCOUNTS.items():
        if not account:
            print("   no account found for %s - skipped" % mode)
            continue
        if not frappe.db.exists("Mode of Payment", mode):
            frappe.get_doc({
                "doctype": "Mode of Payment", "mode_of_payment": mode,
                "type": "Cash" if mode == "Cash" else "Bank", "enabled": 1,
            }).insert(ignore_permissions=True)
        doc = frappe.get_doc("Mode of Payment", mode)
        if not any(a.company == COMPANY for a in doc.accounts):
            doc.append("accounts", {"company": COMPANY, "default_account": account})
            doc.save(ignore_permissions=True)
            done.append((mode, account))
    frappe.db.commit()
    print("mode of payment accounts set:")
    for mode, account in done:
        print("   %-16s -> %s" % (mode, account))
    if not done:
        print("   (already configured)")
    return done


def _cost_centre_for(branch):
    override = COST_CENTRE_OVERRIDES.get(branch)
    if override and frappe.db.exists("Cost Center", override):
        return override
    cc = "%s - %s" % (branch, ABBR)
    return cc if frappe.db.exists("Cost Center", cc) else None


def build_pos_v2(apply=False):
    """POS profiles, second pass: payment modes configured and the Mungwi
    cost-centre override applied."""
    modes = [m for m in ("Cash", "Airtel Money", "MTN MoMo")
             if frappe.db.exists("Mode of Payment", m)]
    created, skipped, errors, no_cc = 0, 0, [], []

    for b in _branches():
        name = "%s POS" % b["branch"]
        if frappe.db.exists("POS Profile", name):
            skipped += 1
            continue
        cc = _cost_centre_for(b["branch"])
        if not cc:
            no_cc.append(b["branch"])
            continue
        if not apply:
            created += 1
            continue
        try:
            frappe.get_doc({
                "doctype": "POS Profile",
                "name": name,
                "company": COMPANY,
                "warehouse": b["warehouse"],
                "cost_center": cc,
                "write_off_cost_center": cc,
                "income_account": POS_INCOME,
                "write_off_account": POS_WRITE_OFF,
                "selling_price_list": POS_PRICE_LIST,
                "currency": "ZMW",
                "disabled": 0,
                "payments": [
                    {"mode_of_payment": m, "default": 1 if i == 0 else 0}
                    for i, m in enumerate(modes)
                ],
            }).insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            errors.append((name, str(e)[:110]))

    if apply:
        frappe.db.commit()
    print("=" * 64)
    print("POS PROFILES v2 - %s" % ("APPLIED" if apply else "PREVIEW"))
    print("=" * 64)
    print("profiles created : %d" % created)
    print("already present  : %d" % skipped)
    print("no cost centre   : %s" % (", ".join(no_cc) or "none"))
    print("payment modes    : %s" % ", ".join(modes))
    print("errors           : %d" % len(errors))
    for name, err in errors[:10]:
        print("   FAIL %-22s %s" % (name, err))
    return {"created": created, "errors": len(errors)}


def apply_pos_v2():
    setup_payment_modes()
    print()
    return build_pos_v2(apply=True)
