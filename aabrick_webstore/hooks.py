app_name = "aabrick_webstore"
app_title = "Aabrick Webstore"
app_publisher = "Adam & Mukuka"
app_description = "Customizations for AABricks webstore"
app_email = "adam.dawoodjee@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "aabrick_webstore",
# 		"logo": "/assets/aabrick_webstore/logo.png",
# 		"title": "Aabrick Webstore",
# 		"route": "/aabrick_webstore",
# 		"has_permission": "aabrick_webstore.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/aabrick_webstore/css/aabrick_webstore.css"
# app_include_js = "/assets/aabrick_webstore/js/aabrick_webstore.js"

# include js, css files in header of web template
# web_include_css = "/assets/aabrick_webstore/css/aabrick_webstore.css"
# web_include_js = "/assets/aabrick_webstore/js/aabrick_webstore.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "aabrick_webstore/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "aabrick_webstore/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# Frappe resolves the home page from Website Settings first, then this hook,
# and only then falls back to the login page for a guest. Website Settings is
# data and does not travel with a deploy, so the app names its own; an
# explicit setting in the UI still takes precedence.
home_page = "index"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# The navbar and the footer are built from the catalogue rather than from a
# list somebody types out, so the templates need a way to read it.
# A plain dotted path: the alias form, name:path, is parsed as an app name
# here and fails to import. The method takes the function's own name.
jinja = {"methods": ["aabrick_webstore.jinja_helpers.nav_data"]}

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "aabrick_webstore.utils.jinja_methods",
# 	"filters": "aabrick_webstore.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "aabrick_webstore.install.before_install"
# after_install = "aabrick_webstore.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "aabrick_webstore.uninstall.before_uninstall"
# after_uninstall = "aabrick_webstore.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "aabrick_webstore.utils.before_app_install"
# after_app_install = "aabrick_webstore.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "aabrick_webstore.utils.before_app_uninstall"
# after_app_uninstall = "aabrick_webstore.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "aabrick_webstore.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"aabrick_webstore.tasks.all"
# 	],
# 	"daily": [
# 		"aabrick_webstore.tasks.daily"
# 	],
# 	"hourly": [
# 		"aabrick_webstore.tasks.hourly"
# 	],
# 	"weekly": [
# 		"aabrick_webstore.tasks.weekly"
# 	],
# 	"monthly": [
# 		"aabrick_webstore.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "aabrick_webstore.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "aabrick_webstore.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "aabrick_webstore.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["aabrick_webstore.utils.before_request"]
# after_request = ["aabrick_webstore.utils.after_request"]

# Job Events
# ----------
# before_job = ["aabrick_webstore.utils.before_job"]
# after_job = ["aabrick_webstore.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"aabrick_webstore.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


# include js on every website page
# Bump this whenever webstore.js or webstore.css changes: these are served
# without a content hash, so browsers keep a stale copy after bench build.
# Webshop's Website Item controller is subclassed rather than patched, so its
# cart, pricing and breadcrumb work still runs and only the template changes.
override_doctype_class = {
	"Website Item": "aabrick_webstore.overrides.website_item.AABrickWebsiteItem",
	# Subclasses webshop's own override, so its filter engine still runs.
	"Item Group": "aabrick_webstore.overrides.item_group.AABrickItemGroup",
}

ASSET_VERSION = "81"
web_include_js = [
	"/assets/aabrick_webstore/js/webstore.js?v=" + ASSET_VERSION,
	"/assets/aabrick_webstore/js/nav.js?v=" + ASSET_VERSION,
]

# inject analytics tags into the website page head
update_website_context = ["aabrick_webstore.analytics.add_analytics_tags"]

# include css on every website page
web_include_css = "/assets/aabrick_webstore/css/webstore.css?v=" + ASSET_VERSION

# Retired pages. /home in particular must be redirected rather than left alone:
# once its Web Page is unpublished, a built-in www/home.html takes over and
# renders an empty page with HTTP 200, which is a soft 404.
# /tile-fix and /fertilizer are deliberately absent: those routes belong to
# Item Groups with real category pages, and a redirect here would shadow them.
website_redirects = [
	{"source": "/home", "target": "/"},
	{"source": "/home2", "target": "/"},
	{"source": "/pages/myhome", "target": "/"},
	{"source": "/pages/my-page-e297", "target": "/"},
	{"source": "/locations", "target": "/branches"},
	{"source": "/about-us", "target": "/"},
	{"source": "/fertilizers", "target": "/all-products"},
	{"source": "/wall-tiles", "target": "/all-products"},
	{"source": "/floor-tiles", "target": "/all-products"},
	{"source": "/matt-tiles", "target": "/all-products"},
	{"source": "/Shiny-tiles", "target": "/all-products"},
	{"source": "/building-materials", "target": "/all-products"},
	{"source": "/live-stock-availability-list", "target": "/all-products"},
	{"source": "/tile-visualizer", "target": "/tile-calculator"},
	{"source": "/gifts", "target": "/"},
	{"source": "/agritech-voucher", "target": "/"},
	{"source": "/agritech-voucher1", "target": "/"},
]
