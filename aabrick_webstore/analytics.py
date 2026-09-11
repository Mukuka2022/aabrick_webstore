"""Web analytics for the AABrick storefront.

Frappe ships a built-in "Google Analytics ID" field, but it emits the old
Universal Analytics snippet (analytics.js / ga('create')), which Google shut
down in July 2023. Filling that field produces the appearance of tracking and
no data. This module installs GA4 and Google Tag Manager properly instead.

Tags are injected server-side into the page head via the update_website_context
hook, so they load early and stay in version control rather than being pasted
into a database settings field.

    bench --site www.aabrick.com execute aabrick_webstore.analytics.install
    bench --site www.aabrick.com execute aabrick_webstore.analytics.status
"""

import frappe
import frappe.website.serve

SETTINGS = "Web Analytics Settings"
MODULE = "Aabrick Webstore"


# --------------------------------------------------------------- setup
def install():
    """Create the settings doctype. Safe to re-run."""
    if frappe.db.exists("DocType", SETTINGS):
        print("%s already exists" % SETTINGS)
        return

    frappe.get_doc({
        "doctype": "DocType",
        "name": SETTINGS,
        "module": MODULE,
        "issingle": 1,
        "custom": 0,
        "track_changes": 1,
        "fields": [
            {"fieldname": "enabled", "label": "Enable Tracking",
             "fieldtype": "Check", "default": "1",
             "description": "Turn off to remove all tags site-wide."},
            {"fieldname": "sec_ids", "label": "Tag IDs", "fieldtype": "Section Break"},
            {"fieldname": "gtm_container_id", "label": "Google Tag Manager Container ID",
             "fieldtype": "Data",
             "description": "Looks like GTM-XXXXXXX. Preferred: manage GA4, Ads and Meta inside GTM without code changes."},
            {"fieldname": "ga4_measurement_id", "label": "GA4 Measurement ID",
             "fieldtype": "Data",
             "description": "Looks like G-XXXXXXXXXX. Only needed if you are not using Tag Manager."},
            {"fieldname": "meta_pixel_id", "label": "Meta Pixel ID",
             "fieldtype": "Data",
             "description": "Numeric. Leave blank if managing Meta inside GTM."},
            {"fieldname": "sec_opts", "label": "Options", "fieldtype": "Section Break"},
            {"fieldname": "track_ecommerce", "label": "Track E-commerce Events",
             "fieldtype": "Check", "default": "1",
             "description": "Sends view_item, add_to_cart and begin_checkout to the data layer."},
            {"fieldname": "anonymize_ip", "label": "Anonymise IP Addresses",
             "fieldtype": "Check", "default": "1"},
        ],
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1},
            {"role": "Website Manager", "read": 1, "write": 1},
        ],
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("created %s" % SETTINGS)


def _settings():
    try:
        return frappe.get_cached_doc(SETTINGS)
    except Exception:
        return None


# --------------------------------------------------------------- injection
def _clean(value):
    """IDs are pasted by hand, and a stray space breaks the tag URL silently.

    A trailing space turns gtm.js?id=GTM-XXXXXXX into ...GTM-XXXXXXX%20, which
    Google rejects, and nothing is ever recorded. Strip defensively on read.
    """
    return (value or "").strip()


def add_analytics_tags(context):
    """update_website_context hook: append tags to the page head."""
    s = _settings()
    if not s or not s.enabled:
        return context

    gtm = _clean(s.gtm_container_id)
    ga4 = _clean(s.ga4_measurement_id)
    pixel = _clean(s.meta_pixel_id)

    parts = []

    if gtm:
        parts.append(_gtm(gtm))
    if ga4 and not gtm:
        parts.append(_ga4(ga4, s.anonymize_ip))
    if pixel:
        parts.append(_meta(pixel))

    if not parts:
        return context

    # always give the storefront script a data layer to push into
    head = ['<script>window.dataLayer = window.dataLayer || [];</script>']
    head.extend(parts)
    head.append('<script>window.aabTrackEcommerce = %s;</script>'
                % ("true" if s.track_ecommerce else "false"))

    context.head_include = (context.get("head_include") or "") + "\n".join(head)
    return context


def _gtm(container):
    return (
        "<!-- Google Tag Manager -->\n"
        "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
        "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
        "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
        "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;"
        "f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','%s');</script>"
        "\n<!-- End Google Tag Manager -->" % container
    )


def _ga4(measurement_id, anonymize):
    anon = ", { 'anonymize_ip': true }" if anonymize else ""
    return (
        "<!-- GA4 -->\n"
        '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}gtag('js',new Date());"
        "gtag('config','%s'%s);</script>\n<!-- End GA4 -->"
        % (measurement_id, measurement_id, anon)
    )


def _meta(pixel_id):
    return (
        "<!-- Meta Pixel -->\n"
        "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){"
        "n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
        "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];"
        "t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
        "s.parentNode.insertBefore(t,s)}(window,document,'script',"
        "'https://connect.facebook.net/en_US/fbevents.js');"
        "fbq('init','%s');fbq('track','PageView');</script>\n"
        "<!-- End Meta Pixel -->" % pixel_id
    )


# --------------------------------------------------------------- diagnostics
def status():
    s = _settings()
    if not s:
        print("%s does not exist yet - run install() first" % SETTINGS)
        return
    print("=" * 58)
    print("WEB ANALYTICS STATUS")
    print("=" * 58)
    print("enabled              : %s" % bool(s.enabled))
    for label, field in (("GTM container", "gtm_container_id"),
                         ("GA4 measurement id", "ga4_measurement_id"),
                         ("Meta pixel", "meta_pixel_id")):
        raw = s.get(field) or ""
        flag = "   <-- has stray whitespace" if raw != raw.strip() else ""
        print("%-20s : %s%s" % (label, _clean(raw) or "(not set)", flag))
    print("ecommerce events     : %s" % bool(s.track_ecommerce))

    legacy = frappe.db.get_single_value("Website Settings", "google_analytics_id")
    print("\nlegacy UA field      : %s" % (legacy or "(empty - good)"))
    if legacy:
        print("  WARNING: that field emits Universal Analytics, dead since July 2023.")
        print("  It collects nothing. Clear it to avoid loading a useless script.")

    configured = bool(s.enabled and (_clean(s.gtm_container_id)
                                     or _clean(s.ga4_measurement_id)
                                     or _clean(s.meta_pixel_id)))
    print("\nconfigured           : %s" % configured)
    if not configured:
        print("  Nothing is being tracked. Paste a GTM container ID or GA4")
        print("  measurement ID into Web Analytics Settings to switch it on.")
        return False

    # Configured is not the same as reaching the page. Every page we write
    # declares its own head_include block, and a Jinja block replaces the
    # parent's rather than adding to it, so a page that forgets super()
    # silently throws these tags away. Render one and look.
    print("\nrendered into the page:")
    missing = []
    for route in _SAMPLE:
        found = _in_page(route)
        print("  %-44s %s" % (route or "/", "yes" if found else "NO"))
        if not found:
            missing.append(route)

    if missing:
        print("\n  Configured but not reaching %d of %d pages checked."
              % (len(missing), len(_SAMPLE)))
        print("  Each of those templates declares {% block head_include %}")
        print("  without {{ super() }}, which discards it.")
    return not missing


# One page of each kind we render, because they inherit differently.
_SAMPLE = (
    # The home page is reached as index here: the empty route only
    # resolves inside a real request, and this runs from the console.
    "index",
    "all-products",
    "branches",
    "contact",
    "tile-calculator",
    "guides",
)


def _in_page(route):
    """Does a rendered page actually carry the tag?"""
    needle = _clean(_settings().gtm_container_id) or _clean(
        _settings().ga4_measurement_id)
    if not needle:
        return False
    try:
        html = frappe.website.serve.get_response_content(route)
    except Exception as e:
        print("     could not render %r: %s" % (route or "/", e))
        return False
    return needle in html


def trim_ids():
    """Strip stray whitespace from stored IDs.

    A pasted trailing space turns gtm.js?id=GTM-XXXXXXX into ...%20, which
    Google rejects silently. add_analytics_tags() strips on read, so this is
    only tidying the stored value; run it after anyone edits the settings.
    """
    fields = ("gtm_container_id", "ga4_measurement_id", "meta_pixel_id")
    changed = []
    for f in fields:
        raw = frappe.db.get_single_value(SETTINGS, f) or ""
        if raw != raw.strip():
            frappe.db.set_single_value(SETTINGS, f, raw.strip())
            changed.append((f, len(raw), len(raw.strip())))
    frappe.db.commit()
    frappe.clear_cache()
    for f, before, after in changed:
        print("trimmed %-22s %d -> %d chars" % (f, before, after))
    if not changed:
        print("all IDs are clean")
    return len(changed)
