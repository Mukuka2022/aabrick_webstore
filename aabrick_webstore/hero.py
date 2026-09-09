"""Install a homepage hero photograph.

The hero lives in the app rather than the site file store, because site files
are data: they stay behind when the app is deployed to another server. Putting
it in public/images means the photograph travels with the code and a fresh
install looks the same as this one.

Two crops are produced. Desktop is wide, mobile is nearly square, because a
2:1 landscape crop on a phone leaves a strip of photograph too shallow to read
as anything. The browser picks between them with a media query.

Usage, from the bench directory:

    bench --site www.aabrick.com execute \\
        aabrick_webstore.hero.set_hero --args "['/path/to/photo.jpg']"

The path may be a file anywhere on the server, or a site file URL as it
appears after uploading through the ERPNext file manager, e.g.
"/files/shopfront.jpg".
"""

import os
import shutil

import frappe

IMAGES = os.path.join(os.path.dirname(__file__), "public", "images")

DESKTOP = (2400, 1100)
MOBILE = (900, 1000)

# Below this the photograph is being upscaled, and a hero is the one image on
# the page nobody can avoid looking at.
MIN_WIDTH = 1600


def _resolve(path):
    """Accept a filesystem path or a /files/... URL from the file manager."""
    if path.startswith("/files/") or path.startswith("/private/files/"):
        return frappe.get_site_path("public" if path.startswith("/files/") else "", path.lstrip("/"))
    return os.path.expanduser(path)


def _crop(im, size):
    """Scale to fill and crop the overflow, biased slightly above centre so
    faces and skylines survive rather than floors."""
    from PIL import Image

    w, h = size
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (im.width - w) // 2
    top = int((im.height - h) * 0.4)
    return im.crop((left, top, left + w, top + h))


def set_hero(path):
    from PIL import Image

    src = _resolve(path)
    if not os.path.exists(src):
        frappe.throw("No file at %s" % src)

    im = Image.open(src)
    print("source: %s  %sx%s  %s" % (os.path.basename(src), im.width, im.height, im.mode))

    if im.width < MIN_WIDTH:
        print(
            "\nREFUSED: %spx wide, and the hero is rendered up to 2400px.\n"
            "Upscaling it would look soft on every screen wider than a phone.\n"
            "Send a photograph at least %spx wide." % (im.width, MIN_WIDTH)
        )
        return

    if im.height > im.width:
        print("\nNote: this is a portrait photograph. The desktop crop will keep a\n"
              "wide band from the middle of it, which is rarely what you want.")

    im = im.convert("RGB")
    os.makedirs(IMAGES, exist_ok=True)

    for size, name in ((DESKTOP, "hero.jpg"), (MOBILE, "hero-mobile.jpg")):
        out = os.path.join(IMAGES, name)
        _crop(im, size).save(out, "JPEG", quality=80, optimize=True, progressive=True)
        print("  wrote %-18s %sx%-6s %6.0f KB" % (name, size[0], size[1], os.path.getsize(out) / 1024))

    print("\nNow run:  bench build --app aabrick_webstore")
    print("Then hard-refresh the homepage.")


def remove_hero():
    """Go back to the plain charcoal gradient."""
    for name in ("hero.jpg", "hero-mobile.jpg"):
        p = os.path.join(IMAGES, name)
        if os.path.exists(p):
            os.remove(p)
            print("removed %s" % name)
    print("\nNow run:  bench build --app aabrick_webstore")


def preview():
    """What is installed right now."""
    for name in ("hero.jpg", "hero-mobile.jpg"):
        p = os.path.join(IMAGES, name)
        if os.path.exists(p):
            from PIL import Image

            im = Image.open(p)
            print("  %-18s %sx%-6s %6.0f KB" % (name, im.width, im.height, os.path.getsize(p) / 1024))
        else:
            print("  %-18s not installed" % name)
