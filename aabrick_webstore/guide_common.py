"""Shared context for a guide page.

Each guide is a thin index.py that names its slug and calls this, so the
heading, the meta description, the reading time and the cross-links all come
from one list rather than being retyped four times and drifting.
"""

import frappe

from aabrick_webstore.www.guides.index import guides


def build(context, slug):
    all_guides = guides()
    this = next((g for g in all_guides if g.slug == slug), None)
    if not this:
        frappe.throw("Unknown guide: %s" % slug)

    context.aab_heading = this.title
    context.title = "%s | AABrick Zambia" % this.title
    context.aab_description = this.summary
    context.aab_minutes = this.minutes
    context.aab_canonical = frappe.utils.get_url("/guides/%s" % slug)
    context.aab_others = [g for g in all_guides if g.slug != slug]
    context.aab_branch_count = frappe.db.count("Branch Location") or 46
    return context
