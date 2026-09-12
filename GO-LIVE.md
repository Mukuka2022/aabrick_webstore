# Going live — what has to happen on the server

`DEPLOY.md` covers getting the code onto the server. This is everything
that does **not** come with the code, and everything still open.

Replace `SITE` with the real site name throughout.

---

## 1. The settings that must differ from the dev bench

```bash
bench --site SITE set-config developer_mode 0
```

With it on, Frappe writes schema changes back to disk on the server, which
collides with the next `git pull`. It stays **on** on the dev bench and
**off** here.

**`mute_emails` must be off on live.** The dev bench has it on:

```bash
bench --site SITE set-config mute_emails 0
```

It exists on the dev bench only because the AABrick email account cannot
decrypt its own password (2b), and without it nobody can test sign-up at
all: frappe sends the welcome mail inside `user.insert()`, the send
throws, and `signup.py` correctly rolls the whole thing back and deletes
the half-made account. Muted, sign-up returns "Please check your email for
verification" and the account is kept.

On live that same setting would swallow every welcome mail, password reset
and order confirmation silently, with nothing in the Error Log to say so.
Check it before announcing the address:

```bash
bench --site SITE execute frappe.are_emails_muted
```

**The site must be served over HTTPS.** The enquiry form on `/contact`
collects a name and a phone number and posts them in the clear otherwise.

---

## 2. What does not travel with a `git pull`

This is the part that catches people. The code is in git. None of this is.

| Thing | Where it lives | How it gets there |
|---|---|---|
| The 436 products, prices, item groups | database | restore, or the scripts below |
| Product photographs (~44MB) | `sites/SITE/public/files` | copied with a `--with-files` backup |
| **Website Theme** | database | must be applied on the live site, or the layout differs |
| **Web Analytics Settings** (GTM container) | database | re-enter the container id |
| Branch details | database | `load_branches.run` rebuilds them from code |
| Anything uploaded to Website Images | `sites/SITE/public/files` | re-upload, or comes with the backup |

The Website Theme is the one most likely to be forgotten. It is what hides
Frappe's default page headers; without it the pages carry two headings.

---

## 2b. Check the site can still read its own secrets

An `encryption_key` that does not match the database it was restored from
is silent until somebody tries to sign up, and then it reads as a bug in
the website rather than a configuration fault. On this dev bench both
stored secrets are unreadable for exactly that reason.

```bash
bench --site SITE console
```

```python
from frappe.utils.password import get_decrypted_password
for a in frappe.db.sql("SELECT doctype, name, fieldname FROM `__Auth` WHERE encrypted = 1", as_dict=True):
    try:
        get_decrypted_password(a.doctype, a.name, a.fieldname, raise_exception=True)
        print("readable  ", a.doctype, a.name, a.fieldname)
    except Exception:
        print("UNREADABLE", a.doctype, a.name, a.fieldname)
```

Anything unreadable has to be entered again on that server, or the
original `encryption_key` copied into `site_config.json`. The two that
matter here:

- **Email Account / AABrick / password** - outgoing mail. Without it
  nobody can sign up, because the welcome mail cannot be sent, and no
  enquiry notification goes out either. It is a Gmail account, so the
  value is a 16 character **App Password** from Google Account security,
  never the real account password. That account also offers OAuth, which
  stores no password at all.
- **Social Login Key / google / client_secret** - Sign in with Google.
  For a customer on a phone, tapping a Google button beats inventing a
  password and waiting for an email.

## 2b2. One line in posawesome, which stops every Customer saving

Not our app, so it does not come with a `git pull` of this repository and
the live server needs it doing separately.

ERPNext moved `get_party_bank_account` out of `erpnext.accounts.party`
and into the Bank Account doctype. posawesome 15.9.2 follows it in
`api/payment_entry.py` and does not in `api/payments.py`, so importing
`posawesome.posawesome.api` raises `ImportError`. posawesome hooks
`Customer` on validate and after_insert, so that import runs on **every
Customer save anywhere**: the desk, the POS, and the website, where
webshop creates a Customer the first time a signed-in shopper opens the
cart. On the website it surfaces as a 500, Uncaught Server Exception.

Check whether the live server has it:

```bash
grep -rn "from erpnext.accounts.party import get_party_bank_account" \
  ~/frappe-bench/apps/posawesome
```

If that prints a line, edit `apps/posawesome/posawesome/posawesome/api/payments.py`
and change that import to:

```python
from erpnext.accounts.doctype.bank_account.bank_account import (
    get_party_bank_account,
)
```

then `bench restart`. Confirm with a Customer save:

```bash
bench --site SITE console
```

```python
d = frappe.get_doc("Customer", frappe.db.get_value("Customer", {}, "name"))
d.save(ignore_permissions=True); frappe.db.rollback(); print("saved fine")
```

**This belongs upstream**, in the posawesome fork at
github.com/dawoodjee/posawesome, or it comes back the next time that app
is pulled or reinstalled.

### There is no newer posawesome to upgrade to

Checked, so nobody has to look again. The fork at
github.com/dawoodjee/posawesome has one branch, no tags, and is zero
commits ahead of what is installed: October 2025 is its tip. The project
it came from, github.com/yrestom/POS-Awesome, was last touched in
February 2024 and has nothing past version-14. What is installed is
already the newest build in that line.

The one line is also the only thing wrong at import level: all 79 modules
in the app import cleanly against ERPNext 15.121.0 once it is corrected.
That is worth knowing, because the usual worry with a fix like this is
that it only uncovers the next break.

It proves the imports, not the till. A function whose signature changed
would import fine and fail in a cashier's hands. Before ERPNext on live
is updated, POSAwesome needs a real pass at a till: ring up a sale, take
a payment, close a shift.

### Why live looks fine today

Because live is on an older ERPNext. The dev bench was built on
2026-09-07 and runs ERPNext 15.121.0, where `get_party_bank_account` is
not in `accounts/party.py` at all. posawesome 15.9.2 was last touched in
October 2025 and was written against an ERPNext that still had it there.

So this is not a dev-only fault. It is what live does the first time it
is updated, and the website is the least of it: every Customer save
across all 46 branches goes, including the POS. Fix the fork **before**
updating ERPNext on live.

Worth knowing while you are there: the ERPNext checkout on the dev bench
is a single squashed commit labelled "ERPNext v15 baseline" rather than a
real clone, so `bench update` cannot pull ERPNext fixes there and there is
no history to read. Dev and live being on different platforms also means
code proven on the bench is not proven against what live runs. Compare
them:

```bash
grep -m1 __version__ ~/frappe-bench/apps/erpnext/erpnext/__init__.py
grep -m1 __version__ ~/frappe-bench/apps/frappe/frappe/__init__.py
```

## 2b3. The Customer Group that stops a customer logging in

This one is data, not code, and a `git pull` will not touch it.

`All Customer Groups` is the root of the Customer Group tree, so it is a
group node, and ERPNext refuses to file a customer against it. Webshop
does not know that. When a customer signs in, webshop appends a Portal
User row to their Customer record and saves it, and the save throws:

```
ValidationError: Cannot select a Group type Customer Group.
Please select a non-group Customer Group.
```

The throw happens inside `on_session_creation`, which means the login
transaction itself dies. There is no session, so no cart, no price list
and no totals. What a customer sees is an error on sign-in, or a cart with
no amounts in it, which is what was reported and chased through the
website code for half a day before anyone looked at the data.

On the dev bench, two things are in that state:

- `Webshop Settings.default_customer_group` is `All Customer Groups`, so
  every new sign-up is stamped with the invalid value
- 23 of 112 customers sit in `All Customer Groups`, and all 23 are
  exactly the ones with an enabled website login

Check live before changing anything:

```bash
bench --site www.aabrick.com mariadb -e "
  SELECT c.customer_group, COUNT(*)
  FROM \`tabCustomer\` c
  JOIN \`tabCustomer Group\` g ON g.name = c.customer_group
  WHERE g.is_group = 1
  GROUP BY c.customer_group;"
```

If live returns nothing, live is clean today. It will not stay clean: the
default setting keeps stamping new sign-ups, and a customer created that
way only fails once something saves them again.

The fix is two values. Pick the non-group to use first; `E-Commerce`
already exists and keeps web customers separable in reports, and
`Individual` is the other sensible answer.

Do it in `bench --site www.aabrick.com console`, rather than by hand in the
desk, so the 23 move together:

```python
group = "E-Commerce"   # decide this before running

s = frappe.get_single("Webshop Settings")
s.default_customer_group = group
s.save()

bad = frappe.db.sql_list("""
    SELECT c.name FROM `tabCustomer` c
    JOIN `tabCustomer Group` g ON g.name = c.customer_group
    WHERE g.is_group = 1
""")
for name in bad:
    frappe.db.set_value("Customer", name, "customer_group", group)
print("moved", len(bad), "customers to", group)
frappe.db.commit()
```

`frappe.db.set_value` is deliberate: a full `save()` on those records runs
every Customer hook, and one of those is the posawesome import in 2b2.
Fix that first or the loop stops on the first record.

### Why this surfaced now

Most likely those 23 were created by website sign-up using the bad
default, back when nothing rejected it, and this bench's ERPNext has since
moved while live's has not. That is inference, not proof: the ERPNext
checkout here is one squashed commit, so there is no history to date the
validation against. It fits every symptom, including posawesome breaking
in the same hour.

Treat it as a warning rather than a finding: if it is right, live breaks
this way on its next ERPNext update, and the cheap moment to fix the data
is before that, not after.

---
## 2c. Server Scripts stay off

Four Server Script records sit in the database and all four are disabled.
Two of them are now code in `portal_rules.py`. Do **not** set
`server_script_enabled`: the other two, Stock Availability API and Access
To View Stock as Guest, are whitelisted to guests and return every item
quantity in every warehouse to anyone who asks.

---

## 3. Run once after the first deploy

In order. All are safe to run twice.

```bash
cd ~/frappe-bench

# The Website Images settings page, and the photo field on Branch Location
bench --site SITE execute aabrick_webstore.setup_images.run

# The Website Text settings page, seeded with the wording on the site today
bench --site SITE execute aabrick_webstore.setup_text.run

# The 46 branches: details, then put them on the site
bench --site SITE execute aabrick_webstore.load_branches.run
bench --site SITE execute aabrick_webstore.load_branches.publish

# Carts started before the web prices were loaded price themselves at zero,
# and checkout is enabled. This reprices them.
bench --site SITE execute aabrick_webstore.cart_pricing.repair

# Any published tile pointing at a photograph that is not on disk
bench --site SITE execute aabrick_webstore.fix_missing_images.run

# What a customer needs to be able to use the cart, and the cost fields
# they must not see on the way. Without this, adding to cart fails for
# every signed-in customer with a bare permission error.
bench --site SITE execute aabrick_webstore.shop_permissions.run
```

Then confirm both halves of that last one:

```bash
bench --site SITE execute aabrick_webstore.shop_permissions.check
bench --site SITE execute aabrick_webstore.shop_permissions.check_staff
```

The customer must come back with `cost came back: no`, and the staff
check with `cost still visible: yes`. If the staff one fails, a role has
Item read that this did not know about; re-running fixes it, because the
roles are read from the doctype rather than listed in the script.

If the catalogue is being built by script rather than restored:

```bash
bench --site SITE execute aabrick_webstore.rebuild_nav.run
bench --site SITE execute aabrick_webstore.publish_grades.run
```

---

## 4. Check before telling anyone the address

```bash
# every page answers
for p in / /all-products /branches /contact /guides /tile-calculator \
         /pvc-ceiling-calculater /cart /login; do
  printf "%-28s %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' https://SITE$p)"
done

# the analytics tags actually reach the page, not just the settings
bench --site SITE execute aabrick_webstore.analytics.status
```

`analytics.status` renders a page of each kind and looks for the container
in the output. Every line must say **yes**. If any says no, that template
is missing `{{ super() }}` in its `head_include` block and is throwing the
tags away.

Then, by eye:

- the header is two tiers with a charcoal strip, not the stock Frappe navbar
- `/branches` lists 46 branches grouped by province
- `/login` shows the brand panel beside the form
- **`/cart` with something in it** — the payment summary, Place Order and the
  address picker are drawn by webshop's javascript against a live session and
  have never been seen outside this dev bench
- the site on an actual phone

---

## 5. Still open — content

| | |
|---|---|
| PVC ceiling boards | 96 items, 94 priced, **0 photographs**. Six photos publishes the range. |
| Hero and showcase | the hero is low resolution and the three gallery photos are one placeholder repeated. Upload at `/app/website-images`. |
| 8 WhatsApp numbers | Mansa, Chinsali, Petauke, Mungwi, Silverest, Livingstone, Mazabuka, Monze. Left blank rather than publish a number that belongs to somebody else. |
| 5 branch addresses | Samfya, 9 Miles, Lusaka Great North, Meanwood, Silverest. Four of the five are Lusaka. |
| Tile 56000D | unpublished. Its A grade twin has no photograph to borrow. |
| Adhesive coverage | the guides say "ask your branch" because nobody could say the m² per 20kg bag. |
| 103 product photos | under 600px wide; they go soft on a phone. |

## 6. Still open — decisions

**Adding to cart requires a login.** A guest who clicks Add to cart is sent
to `/login`. For customers arriving on a phone that is a real barrier; most
will leave rather than open an account to price tiles. Decide before launch.

**Does +260 960 787 777 take WhatsApp?** It changes how prominent the
enquiry form should be against a WhatsApp button.

**Google Business.** Kalulushi and Kasama are **suspended**, which means they
do not exist in Maps. Mongu is flagged a duplicate, and Chinsali, Chipata and
Zamtan each have two listings. Twenty-one of the 46 branches have no listing
at all, six of them in Lusaka. Five listings — Mwinilunga, Chama, Kasempa,
Zamtan, Lusaka Chachacha Road — have no branch in the worksheet.

**Two possible data faults, not touched.** Tile 96000 shows
`/files/56111.jpg` while 56111 shows `/files/Black.jpg`; that pair looks
shifted by a row, which would mean both show the wrong tile. And Chinsali's
address now reads "Green Road" from Google, where the worksheet had the more
useful "Green farm road next to PK guest house".

---

## 7. The rule for the live server

Nothing is edited here. It changes on the dev bench, gets tested, gets
pushed, and this server pulls it. Anything edited directly on the server is
lost at the next `git pull` and will not be in the next release.
