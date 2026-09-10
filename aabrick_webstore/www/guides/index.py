"""The guides.

The brief asks the site to teach, not only to sell, and to organise that around
what people actually search: which tile for which room, what the sizes mean,
how much to buy, how it goes down.

Written as data rather than as four hand-built pages, so the index, the
navigation and the cross-links between them stay in step with each other. Each
guide renders through one template.

Everything factual here comes from the catalogue or from the client: the sizes
and finishes are the item groups, the 7 day lead time and the branch count are
the same figures the rest of the site uses. Where a claim would need trade
knowledge we do not have on record, the guide points at a branch instead of
inventing a number.
"""

import frappe

no_cache = 1
sitemap = 1


def guides():
    """One entry per guide. route is under /guides/."""
    return [
        frappe._dict({
            "slug": "choosing-tiles",
            "title": "Which tile for which room",
            "nav": "Choosing tiles",
            "summary": (
                "Porcelain, glazed, matt or polished, and where each one belongs. "
                "The differences that matter when you are standing in the shop."
            ),
            "minutes": 4,
        }),
        frappe._dict({
            "slug": "tile-sizes",
            "title": "Tile sizes explained",
            "nav": "Tile sizes",
            "summary": (
                "What 600x600 means, how size changes a room, and which of our "
                "sizes suits a floor, a wall or a small bathroom."
            ),
            "minutes": 3,
        }),
        frappe._dict({
            "slug": "how-much-to-buy",
            "title": "How much to buy",
            "nav": "How much to buy",
            "summary": (
                "Working out boxes from a room, why you order spare, and why the "
                "whole job should come from one delivery."
            ),
            "minutes": 3,
        }),
        frappe._dict({
            "slug": "laying-tiles",
            "title": "Laying tiles",
            "nav": "Laying tiles",
            "summary": (
                "Preparing the surface, choosing adhesive and grout, and the "
                "mistakes that cost the most to put right."
            ),
            "minutes": 5,
        }),
    ]


def get_context(context):
    context.title = "Guides | AABrick Zambia"
    context.aab_description = (
        "Plain guidance on choosing, buying and laying tiles in Zambia. Which "
        "tile for which room, what the sizes mean, how much to buy, and how it "
        "goes down."
    )
    context.aab_canonical = frappe.utils.get_url("/guides")
    context.aab_guides = guides()
    context.aab_branch_count = frappe.db.count("Branch Location") or 46
    return context
