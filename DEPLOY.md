# AABrick website — deployment runbook

For whoever administers the live Frappe/ERPNext server. Nothing in here is
development work: the app is built and tested elsewhere, pushed to GitHub, and
this server only ever pulls it.

Replace `SITE` throughout with the real site name on that bench (the folder
under `sites/`, e.g. `aabrick.com`).

---

## 0. Before you start

Run these two and send the output back before doing anything else.

```bash
cd ~/frappe-bench
cat sites/apps.txt
bench version
```

The site depends on **nine** apps. If any of these are missing from
`apps.txt`, step 2 will fail:

| app | branch | source |
|---|---|---|
| frappe | version-15 | https://github.com/frappe/frappe.git |
| erpnext | version-15 | (standard) |
| webshop | version-15 | https://github.com/frappe/webshop.git |
| payments | version-15 | https://github.com/frappe/payments.git |
| hrms | version-15 | https://github.com/frappe/hrms.git |
| posawesome | — | https://github.com/dawoodjee/posawesome |
| builder | — | https://github.com/frappe/builder.git |
| flex | main | https://github.com/fabricverse/flex |
| **aabrick_webstore** | main | https://github.com/Mukuka2022/aabrick_webstore |

`webshop` is the one that matters most — `aabrick_webstore` subclasses its
doctypes and will not import without it.

The dev bench runs Python 3.10.12 and Node 18. Node 18 or newer is needed for
`bench build`.

---

## 1. Take a backup first

Always, before the first deploy and before every later one.

```bash
cd ~/frappe-bench
bench --site SITE backup --with-files
```

It prints where it wrote the files. Keep that path — step 6 is how you undo.

---

## 2. Get the app

**First time on this bench:**

```bash
cd ~/frappe-bench
bench get-app aabrick_webstore https://github.com/Mukuka2022/aabrick_webstore --branch main
bench --site SITE install-app aabrick_webstore
```

**Every time after that:**

```bash
cd ~/frappe-bench/apps/aabrick_webstore
git pull origin main
```

---

## 3. Apply it

```bash
cd ~/frappe-bench
bench --site SITE migrate
bench build --app aabrick_webstore
bench --site SITE clear-cache
bench restart
```

`bench restart` assumes supervisor. If the bench is run some other way,
restart it however this server normally does.

---

## 4. The catalogue

The code carries no products. The 436 published items, the 46 branch records,
the item groups and about 44MB of product images all live in the database and
in `sites/SITE/public/files`, so they arrive one of two ways. **Ask before
choosing** — this is the one decision that is not ours to make.

**Option A — restore the dev database.** Right when the live server has no
real ERP data on it yet. A `--with-files` archive is supplied separately
(~60MB).

```bash
bench --site SITE restore /path/to/backup.sql.gz \
  --with-public-files /path/to/files.tar
```

> The `encryption_key` in `sites/SITE/site_config.json` must match the one the
> backup was taken with, or stored passwords and API keys come back unreadable.
> If the site already has its own key, keep it and expect to re-enter those.

**Option B — leave the live database alone** and load the catalogue into it
with the scripts that ship inside the app. Right when the server already
carries real ERP data that must not be overwritten. They are written to be
safe to run twice.

```bash
bench --site SITE execute aabrick_webstore.rebuild_nav.run
bench --site SITE execute aabrick_webstore.publish_grades.run
```

Product images still have to be copied into `sites/SITE/public/files`
separately under Option B.

---

## 5. Check it worked

```bash
cd ~/frappe-bench
curl -s -o /dev/null -w '%{http_code}\n' https://SITE/
curl -s https://SITE/ | grep -c 'aab-nav-main'      # expect 1
curl -s https://SITE/ | grep -c 'navbar-expand-lg'  # expect 0
curl -s -o /dev/null -w '%{http_code}\n' https://SITE/all-products
curl -s -o /dev/null -w '%{http_code}\n' https://SITE/tile-calculator
```

All the codes should be 200. If the homepage serves a login page instead of
the shop, the site's `home_page` in Website Settings has been cleared — the
app sets a fallback in code, so `bench --site SITE clear-cache` usually
settles it.

Then open the site on a phone. The header should be a two-tier bar with a
charcoal strip on top, not the stock Frappe navbar.

---

## 6. If it goes wrong

```bash
cd ~/frappe-bench
bench --site SITE restore /path/from/step/1.sql.gz
bench --site SITE clear-cache
bench restart
```

To back out only the code, check the app out at the previous commit and run
step 3 again:

```bash
cd ~/frappe-bench/apps/aabrick_webstore
git log --oneline -5        # pick the commit before this deploy
git checkout <commit>
cd ~/frappe-bench && bench --site SITE migrate && bench build --app aabrick_webstore && bench restart
```

---

## 7. Two settings that must differ from dev

```bash
bench --site SITE set-config developer_mode 0
```

Developer mode is on in the dev bench and must be off here: with it on,
Frappe writes doctype changes back out to disk as files.

And the site must be served over HTTPS. The enquiry form on `/contact`
collects a name and a phone number, and it posts them in the clear otherwise.

---

## Rule for this server

No edits are made here. If something needs changing, it changes on the dev
bench, gets tested, gets pushed to GitHub, and this server pulls it. Anything
edited directly on the server is lost at the next `git pull` and will not be
in the next release.
