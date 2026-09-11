"""The words on the pages we built, in one place.

The wording lived in the templates, which meant nobody at AABrick could
change a headline without us. These are the same sentences, kept here as
the defaults and overridable from the desk at /app/website-text.

A blank field means "use the wording below", so clearing a box restores it
rather than emptying the page. That is also why the defaults live here and
not only in the database: a fresh install reads the same as this one before
anybody has typed anything.
"""

# key -> (label, current wording, help shown in the desk)
COPY = [
    ("sec_strip", "Above the header", None, None),
    ("strip_line", "The promise line",
     "{branches} branches nationwide &middot; delivery within 7 days",
     "The thin dark strip at the very top. Write {branches} where the "
     "number should go and it fills itself in."),

    ("sec_hero", "The first screen", None, None),
    ("hero_eyebrow", "Small line above the headline",
     "Premium building &amp; finishing materials", None),
    ("hero_line_1", "Headline, first line", "Building Zambia", None),
    ("hero_line_2", "Headline, second line", "Beautifully",
     "Shown in red, under the first line."),
    ("hero_lede", "Paragraph under the headline",
     "Tiles, tile fix, PVC ceiling boards and fertilizer. Trusted by "
     "contractors, homeowners and farmers since 2005.", None),
    ("hero_button_1", "Red button", "Shop online", None),
    ("hero_button_2", "Outline button", "Find a branch", None),

    ("sec_cat", "Shop by category", None, None),
    ("category_eyebrow", "Small line", "Shop by category", None),
    ("category_heading", "Heading", "Find what you need", None),

    ("sec_panels", "The two coloured panels", None, None),
    ("panel_1_eyebrow", "Red panel, small line", "Shop online", None),
    ("panel_1_heading", "Red panel, heading",
     "Your finishing needs, a click away", None),
    ("panel_1_text", "Red panel, paragraph",
     "Browse the full range, see prices, and order for delivery or "
     "collection at your nearest branch.", None),
    ("panel_2_eyebrow", "Dark panel, small line", "Need a hand?", None),
    ("panel_2_heading", "Dark panel, heading",
     "Work out exactly how much you need", None),
    ("panel_2_text", "Dark panel, paragraph",
     "Our tile and PVC ceiling calculators tell you how many boxes or "
     "boards to buy, before you spend anything.", None),

    ("sec_rail", "Finished with AABrick", None, None),
    ("rail_eyebrow", "Small line", "Shop by room", None),
    ("rail_heading", "Heading", "Finished with AABrick", None),
    ("rail_lede", "Paragraph",
     "Tiles, tile fix and PVC ceiling boards, in the rooms they end up in.",
     None),

    ("sec_popular", "Popular right now", None, None),
    ("popular_eyebrow", "Small line", "From the range", None),
    ("popular_heading", "Heading", "Popular right now", None),

    ("sec_why", "Why choose AABrick", None, None),
    ("why_eyebrow", "Small line", "Why choose AABrick", None),
    ("why_heading", "Heading", "Twenty years supplying Zambia", None),

    ("sec_branch", "The branch band", None, None),
    ("branch_heading", "Heading", "There is a branch near you", None),
    ("branch_text", "Paragraph",
     "Come and see the tiles in person, or call and we will tell you what "
     "is on the shelf today.", None),

    ("sec_talk", "Talk to us", None, None),
    ("talk_eyebrow", "Small line", "Talk to us", None),
    ("talk_heading", "Heading", "However you prefer to buy", None),

    ("sec_foot", "Footer", None, None),
    ("footer_blurb", "The paragraph under the company name",
     "Tiles, tile fix, PVC ceiling boards and fertilizer, supplied across "
     "Zambia since 2005. Anything not on the shelf is ordered from the "
     "manufacturer and delivered within 7 days.", None),
]

# Anything longer than a headline gets a box rather than a line.
LONG = {"hero_lede", "panel_1_text", "panel_2_text", "rail_lede",
        "branch_text", "footer_blurb"}

DEFAULTS = {k: v for k, _l, v, _h in COPY if v is not None}
