// Desk tweaks.
//
// Loaded through app_include_js, which Frappe concatenates in app order, so
// this runs after frappe's own toolbar and can replace what it defined.

(function () {
	"use strict";

	// View Website went nowhere.
	//
	// Frappe opens a blank tab first and then tries to steer it:
	//
	//     let website_tab = window.open();
	//     website_tab.opener = null;
	//     website_tab.location = "/index";
	//
	// A popup blocker sees window.open() with no address and stops it, and
	// where it is allowed through the user is left looking at about:blank
	// while the second line quietly fails. Opening the address in the one
	// call is what a blocker actually permits, because it is plainly the
	// click doing it.
	//
	// It also asked for /index rather than /. Both serve the home page, but
	// / is the address customers use and the one worth putting in front of
	// whoever is looking.
	function patchViewWebsite() {
		if (!window.frappe || !frappe.ui || !frappe.ui.toolbar) {
			return false;
		}
		frappe.ui.toolbar.view_website = function () {
			window.open("/", "_blank", "noopener");
		};
		return true;
	}

	if (patchViewWebsite()) {
		return;
	}

	// The toolbar is not up yet. Look again for a while, then give up rather
	// than leave a timer running for the life of the session.
	var tries = 0;
	var timer = setInterval(function () {
		tries += 1;
		if (patchViewWebsite() || tries > 100) {
			clearInterval(timer);
		}
	}, 100);
})();
