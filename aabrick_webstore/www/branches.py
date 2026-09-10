"""Context for /branches - the branch directory."""

import frappe

no_cache = 1
sitemap = 1


def get_context(context):
	branches = frappe.get_all(
		"Branch Location",
		filters={"published": 1},
		fields=["branch_name", "route", "province", "region", "city",
		        "street_address", "phone"],
		order_by="province asc, branch_name asc",
	)

	by_province = {}
	for b in branches:
		by_province.setdefault(b.province or "Other", []).append(b)

	context.branches = branches
	context.by_province = sorted(by_province.items())
	context.branch_count = len(branches)
	context.total_branches = frappe.db.count("Branch Location")
	context.company_phone = "+260 960 787 777"
	context.title = "Our Branches"
	context.description = (
		"AABrick has branches across Zambia stocking tiles, tile fix, "
		"PVC ceiling boards and fertilizer. Find your nearest branch."
	)
	return context
