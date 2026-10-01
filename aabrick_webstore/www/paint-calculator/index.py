"""The paint calculator.

AABrick does not sell paint. There is not a tin of it in the catalogue, so
unlike the other two calculators this one has no shelf rate to price from and
does not pretend to: it works out litres and tins, and the cost line stays
empty until somebody types in what they are paying. Inventing a rate would be
the one thing a calculator must never do.

It earns its place anyway. Somebody tiling a bathroom is painting the rest of
it, and the people who need this are the people already standing in a branch.
If paint is ever stocked, the surfaces and tins below become a query the same
way the tile calculator reads the catalogue.

The coverage figures are per coat, on the surface named, and they are the
conservative end of what manufacturers print. A tin that claims 14 is quoting
a roller on new skimmed plaster in a laboratory; the same tin on a Zambian
block wall in the dry season does nothing of the sort. Each one is editable,
because the number on the tin in front of the customer beats the number here.
"""

import frappe

no_cache = 1
sitemap = 1

# Square metres a litre covers, for one coat. The conservative end of the
# printed range: under-ordering paint means a second trip and a batch that
# does not match.
SURFACES = [
    {"key": "painted", "label": "Painted already, smooth", "cover": 13.0,
     "note": "A repaint over sound emulsion. The surface takes the least."},
    {"key": "plaster", "label": "New plaster or skimmed", "cover": 11.0,
     "note": "Fresh plaster drinks the first coat. Allow a mist coat."},
    {"key": "rough", "label": "Rough or textured plaster", "cover": 8.5,
     "note": "Texture is surface area. It takes far more than it looks."},
    {"key": "block", "label": "Bare block or brick", "cover": 6.5,
     "note": "Porous and uneven. Seal it first or it will drink two coats."},
]

# The sizes paint is sold in here. No prices: see the note at the top.
TINS = [
    {"litres": 1.0, "label": "1 litre"},
    {"litres": 5.0, "label": "5 litres"},
    {"litres": 20.0, "label": "20 litres"},
]

# Deducted per opening, and editable on the page. A standard door leaf and a
# window that is neither the smallest nor the largest in a Zambian house.
DOOR_M2 = 1.8
WINDOW_M2 = 1.44


def get_context(context):
    context.title = "Paint Calculator | AABrick Zambia"
    context.aab_description = (
        "Work out how much paint a room needs. Enter the walls, take off the "
        "doors and windows, choose the surface and the number of coats, and "
        "this works out the litres and the tins."
    )
    context.aab_canonical = frappe.utils.get_url("/paint-calculator")

    context.aab_surfaces = SURFACES
    context.aab_surfaces_json = frappe.as_json(SURFACES)
    context.aab_tins = TINS
    context.aab_tins_json = frappe.as_json(TINS)
    context.aab_door = DOOR_M2
    context.aab_window = WINDOW_M2
    context.aab_branch_count = frappe.db.count("Branch Location") or 46

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
