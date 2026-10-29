"""Compare two ERPNext structures and say what can actually be done.

    python erp_plan.py <live-audit.json> <dev-audit.json> [out.csv]

Both files come from `aabrick_webstore.erp_audit.export`. The first is the
server being changed, the second is the structure wanted.

The question this answers is not "what is different" -- a diff does that and
is useless on its own. It is "what is different AND may be touched", because
on a live ledger those are not the same set. A record carrying posted
transactions cannot be deleted at all, and renaming one rewrites every
historical document that points at it. So every difference is sorted into
what the ledger permits, not what the structure wants.
"""

import csv
import io
import json
import re
import sys
from collections import OrderedDict

# fields whose disagreement is a real difference rather than noise
COMPARE = {
    "Account": ["_parent", "is_group", "root_type", "report_type",
                "account_type", "account_number"],
    "Cost Center": ["_parent", "is_group"],
    "Warehouse": ["_parent", "is_group"],
    "Mode of Payment": ["type", "enabled"],
    "Item Group": ["_parent", "is_group"],
}


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def stem(name):
    """A name with the company suffix taken off, for matching across benches."""
    return re.sub(r"\s+-\s+[A-Z]{2,5}$", "", name or "").strip().lower()


def classify(live, dev, dt):
    """Sort every record of one doctype into what may be done with it."""
    lrows = {r["name"]: r for r in live["doctypes"].get(dt, {}).get("rows", [])}
    drows = {r["name"]: r for r in dev["doctypes"].get(dt, {}).get("rows", [])}

    same_name = set(lrows) & set(drows)
    only_live = set(lrows) - set(drows)
    only_dev = set(drows) - set(lrows)

    # A record missing by name may be the same thing under another suffix or
    # another label. Match on the bare stem first, then report what is left.
    renames = []
    by_stem_dev = {}
    for n in only_dev:
        by_stem_dev.setdefault(stem(n), []).append(n)
    for n in sorted(only_live):
        cand = by_stem_dev.get(stem(n))
        if cand and len(cand) == 1:
            renames.append((n, cand[0], lrows[n]["_used"]))
    renamed_live = {a for a, _, _ in renames}
    renamed_dev = {b for _, b, _ in renames}
    only_live -= renamed_live
    only_dev -= renamed_dev

    changed = []
    for n in sorted(same_name):
        diffs = []
        for f in COMPARE.get(dt, ["_parent"]):
            a, b = lrows[n].get(f), drows[n].get(f)
            if (a or None) != (b or None):
                diffs.append((f, a, b))
        if diffs:
            changed.append((n, lrows[n]["_used"], diffs))

    blocked = sorted((n for n in only_live if lrows[n]["_used"]),
                     key=lambda n: -lrows[n]["_used"])
    free = sorted(n for n in only_live if not lrows[n]["_used"])
    return {
        "live": lrows, "dev": drows,
        "renames": renames, "changed": changed,
        "blocked": blocked, "free": free,
        "create": sorted(only_dev),
    }


def report(live, dev, out_csv=None):
    print("  live : %s   taken %s" % (live.get("site"), live.get("taken")))
    print("  want : %s   taken %s" % (dev.get("site"), dev.get("taken")))
    print("  erpnext %s vs %s"
          % (live.get("versions", {}).get("erpnext"),
             dev.get("versions", {}).get("erpnext")))

    rows_out = []
    for dt in COMPARE:
        if dt not in live.get("doctypes", {}):
            continue
        c = classify(live, dev, dt)
        print("\n" + "=" * 72)
        print("  %s   live %d, wanted %d"
              % (dt.upper(), len(c["live"]), len(c["dev"])))
        print("=" * 72)

        if c["blocked"]:
            print("\n  CANNOT BE REMOVED -- on live, not in the new structure,")
            print("  and carrying posted history. Disable at most.")
            for n in c["blocked"][:40]:
                print("    %-48s %6d rows" % (n[:48], c["live"][n]["_used"]))
            if len(c["blocked"]) > 40:
                print("    ... %d more" % (len(c["blocked"]) - 40))
        if c["free"]:
            print("\n  CAN BE RETIRED -- on live, not wanted, nothing posted (%d)"
                  % len(c["free"]))
            for n in c["free"][:20]:
                print("    %s" % n)
            if len(c["free"]) > 20:
                print("    ... %d more" % (len(c["free"]) - 20))
        if c["create"]:
            print("\n  TO CREATE -- wanted, absent on live (%d)" % len(c["create"]))
            for n in c["create"][:20]:
                print("    %s" % n)
            if len(c["create"]) > 20:
                print("    ... %d more" % (len(c["create"]) - 20))
        if c["renames"]:
            print("\n  LIKELY RENAMES -- same thing, different label (%d)"
                  % len(c["renames"]))
            for a, b, used in c["renames"][:20]:
                flag = "  <- rewrites %d posted rows" % used if used else ""
                print("    %-36s -> %-28s%s" % (a[:36], b[:28], flag))
            if len(c["renames"]) > 20:
                print("    ... %d more" % (len(c["renames"]) - 20))
        if c["changed"]:
            print("\n  SAME NAME, DIFFERENT SHAPE (%d)" % len(c["changed"]))
            for n, used, diffs in c["changed"][:20]:
                bits = ", ".join("%s %s->%s" % (f, a, b) for f, a, b in diffs)
                print("    %-40s %s" % (n[:40], bits[:60]))
            if len(c["changed"]) > 20:
                print("    ... %d more" % (len(c["changed"]) - 20))
        if not any((c["blocked"], c["free"], c["create"],
                    c["renames"], c["changed"])):
            print("\n  identical on both benches")

        for n in c["blocked"]:
            rows_out.append([dt, n, "cannot remove", c["live"][n]["_used"], ""])
        for n in c["free"]:
            rows_out.append([dt, n, "can retire", 0, ""])
        for n in c["create"]:
            rows_out.append([dt, n, "to create", "", ""])
        for a, b, used in c["renames"]:
            rows_out.append([dt, a, "rename", used, b])
        for n, used, diffs in c["changed"]:
            rows_out.append([dt, n, "re-shape", used,
                             "; ".join("%s %s->%s" % d for d in diffs)])

    if out_csv:
        with io.open(out_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["doctype", "record", "verdict",
                        "posted rows", "detail"])
            w.writerows(rows_out)
        print("\n  %d lines written to %s" % (len(rows_out), out_csv))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    report(load(sys.argv[1]), load(sys.argv[2]),
           sys.argv[3] if len(sys.argv) > 3 else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
