"""Diff the operational branch list (supplied 2026-09-08) against ERPNext warehouses."""

import frappe

# (province, branch) exactly as supplied by AABrick
OPERATIONAL = [
    ("Central", "Mkushi"), ("Central", "Kapiri"),
    ("Copperbelt", "Kasumbalesa"), ("Copperbelt", "Mufurila"),
    ("Copperbelt", "Luanshya"), ("Copperbelt", "Ndola 2"),
    ("Copperbelt", "Ndola Main"), ("Copperbelt", "Kitwe Main"),
    ("Copperbelt", "Ndeke"), ("Copperbelt", "Kalulushi"),
    ("Copperbelt", "Chingola"), ("Copperbelt", "Chililiabombwe"),
    ("Eastern", "Chipata"), ("Eastern", "Lundazi"), ("Eastern", "Katete"),
    ("Eastern", "Sinda"), ("Eastern", "Petauke"), ("Eastern", "Nyimba"),
    ("Luapula", "Mansa"), ("Luapula", "Serenje"), ("Luapula", "Kawambwa"),
    ("Luapula", "Luwingu"), ("Luapula", "Samfya"),
    ("Lusaka", "SOS"), ("Lusaka", "Chalala"), ("Lusaka", "Mungwi"),
    ("Lusaka", "Silverest"), ("Lusaka", "Kafue"), ("Lusaka", "Nine Miles"),
    ("Lusaka", "Lusaka Great North"), ("Lusaka", "Meanwood"),
    ("Lusaka", "Garden House"), ("Lusaka", "Kabwe"),
    ("Muchinga", "Chinsali"), ("Muchinga", "Mpika"),
    ("North-Western", "Solwezi"), ("North-Western", "Manyama"),
    ("Northern", "Kasama"),
    ("Southern", "Livingston"), ("Southern", "Choma"), ("Southern", "Monze"),
    ("Southern", "Kalomo"), ("Southern", "Mazabuka"),
    ("Western", "Mongu"), ("Western", "Kaoma"), ("Western", "Senanga"),
]

# supplied spelling -> spelling already in ERPNext (same physical branch)
ALIASES = {
    "mufurila": "Mufulira",
    "chililiabombwe": "Chililabombwe",
    "nine miles": "9 Miles",
    "ndola 2": "Ndola",
    "livingston": "Livingstone",
}


def clean(name):
    n = name
    for suffix in (" - AZL", " - ALZ"):
        while n.endswith(suffix):
            n = n[: -len(suffix)]
    return n.strip()


def run():
    rows = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0},
        fields=["name", "parent_warehouse"],
    )
    in_system = {}
    for r in rows:
        p = r.parent_warehouse or ""
        if p in ("All Warehouses - AZL", "Website Warehouses - AZL", ""):
            continue
        in_system[clean(r.name).lower()] = (clean(r.name), clean(p).replace(" Province", ""), r.name)

    wanted = {}
    for prov, br in OPERATIONAL:
        key = ALIASES.get(br.lower(), br).lower()
        wanted[key] = (br, prov)

    print("=" * 70)
    print("OPERATIONAL LIST: %d branches   |   IN ERPNEXT: %d" % (len(wanted), len(in_system)))
    print("=" * 70)

    print("\n### NEW - create these (%s)" % sum(1 for k in wanted if k not in in_system))
    for k in sorted(wanted):
        if k not in in_system:
            print("   + %-22s  %s" % (wanted[k][0], wanted[k][1]))

    print("\n### NOT OPERATIONAL - in ERPNext but not on your list")
    closing = [k for k in in_system if k not in wanted]
    for k in sorted(closing):
        nm, prov, stored = in_system[k]
        sle = frappe.db.count("Stock Ledger Entry", {"warehouse": stored})
        bins = frappe.db.sql("""SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin`
                                WHERE warehouse=%s""", stored)[0][0]
        pos = frappe.db.count("POS Profile", {"warehouse": stored})
        flag = "  <-- HAS STOCK/TXNS" if (sle or bins or pos) else ""
        print("   - %-22s %-14s  sle=%-4d qty=%-8s pos=%d%s"
              % (nm, prov, sle, bins, pos, flag))
    print("   (%d total)" % len(closing))

    print("\n### PROVINCE MISMATCHES (list vs ERPNext)")
    for k in sorted(wanted):
        if k in in_system:
            nm, prov_sys, _ = in_system[k]
            prov_new = wanted[k][1]
            if prov_sys.lower() != prov_new.lower():
                print("   ~ %-22s  ERPNext=%-16s list=%s" % (nm, prov_sys, prov_new))

    print("\n### SPELLING RECONCILED")
    for supplied, actual in ALIASES.items():
        if actual.lower() in in_system:
            print("   = %-22s -> %s (existing)" % (supplied, actual))
        else:
            print("   ! %-22s -> %s (NOT in ERPNext - treat as new)" % (supplied, actual))
