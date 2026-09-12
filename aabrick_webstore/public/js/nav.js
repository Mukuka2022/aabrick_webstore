/* Navbar behaviour.
 *
 * Pure ASCII: served without a charset.
 *
 * Panels open on click rather than on hover. Hover menus are unusable on a
 * touch screen and awkward for anyone using a keyboard, and this menu has to
 * work on a phone in a branch as much as on a desktop.
 */
(function () {
	"use strict";

	function closeAll(except) {
		var open = document.querySelectorAll(".aab-nav-has-panel.is-open");
		for (var i = 0; i < open.length; i++) {
			if (open[i] !== except) {
				open[i].classList.remove("is-open");
				var b = open[i].querySelector(".aab-nav-link");
				if (b) {
					b.setAttribute("aria-expanded", "false");
				}
			}
		}
	}

	function start() {
		var nav = document.getElementById("aab-nav");
		if (!nav || nav.__aabBound) {
			return;
		}
		nav.__aabBound = true;

		var toggle = document.getElementById("aab-nav-toggle");
		var menu = document.getElementById("aab-nav-menu");

		if (toggle && menu) {
			toggle.addEventListener("click", function () {
				var open = nav.classList.toggle("is-menu-open");
				toggle.setAttribute("aria-expanded", open ? "true" : "false");
				if (!open) {
					closeAll(null);
				}
			});
		}

		var holders = nav.querySelectorAll(".aab-nav-has-panel");
		for (var i = 0; i < holders.length; i++) {
			(function (holder) {
				var btn = holder.querySelector(".aab-nav-link");
				if (!btn) {
					return;
				}
				btn.addEventListener("click", function (e) {
					e.preventDefault();
					var willOpen = !holder.classList.contains("is-open");
					closeAll(holder);
					holder.classList.toggle("is-open", willOpen);
					btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
				});
			})(holders[i]);
		}

		document.addEventListener("click", function (e) {
			if (!nav.contains(e.target)) {
				closeAll(null);
			}
		});

		document.addEventListener("keydown", function (e) {
			if (e.key === "Escape") {
				closeAll(null);
				nav.classList.remove("is-menu-open");
				if (toggle) {
					toggle.setAttribute("aria-expanded", "false");
				}
			}
		});

		// A shadow once the page has moved, so the bar separates from whatever
		// is scrolling under it.
		function onScroll() {
			nav.classList.toggle("is-stuck", window.scrollY > 4);
		}
		window.addEventListener("scroll", onScroll, { passive: true });
		onScroll();
	}

	// The shop filters.
	//
	// They are plain links and they work with no javascript at all, which is
	// why they are not collapsed in the markup: without this file a customer
	// still sees every filter. What this adds is the collapse on a phone,
	// where the filters stack above the grid and would otherwise put six
	// hundred pixels of links between the customer and the first tile.
	function startFilters() {
		var box = document.querySelector(".aab-filters");
		if (!box || box.getAttribute("data-aab-ready")) {
			return;
		}
		box.setAttribute("data-aab-ready", "1");

		var head = box.querySelector(".aab-filters-head");
		var body = box.querySelector(".aab-filters-body");
		var clear = box.querySelector(".aab-clear");
		if (!head || !body) {
			return;
		}

		var chosen = box.querySelectorAll(".aab-filter-group a.is-on").length;
		var btn = document.createElement("button");
		btn.type = "button";
		btn.className = "aab-filters-toggle";
		btn.setAttribute("aria-controls", "aab-filters-body");
		if (clear) {
			head.insertBefore(btn, clear);
		} else {
			head.appendChild(btn);
		}

		function label(open) {
			btn.textContent = open ? "Hide" : "Show";
			if (chosen) {
				var tag = document.createElement("span");
				tag.className = "aab-filters-count";
				tag.textContent = String(chosen);
				btn.appendChild(document.createTextNode(" "));
				btn.appendChild(tag);
			}
		}

		function setOpen(open) {
			body.hidden = !open;
			btn.setAttribute("aria-expanded", open ? "true" : "false");
			label(open);
		}

		var narrow = window.matchMedia("(max-width: 899.98px)");

		function sync() {
			if (narrow.matches) {
				btn.hidden = false;
				// Anything already filtered stays in view, so the customer can
				// see what is narrowing the list and take it off again.
				setOpen(chosen > 0);
			} else {
				btn.hidden = true;
				body.hidden = false;
			}
		}

		btn.addEventListener("click", function () {
			setOpen(body.hidden);
		});

		if (narrow.addEventListener) {
			narrow.addEventListener("change", sync);
		} else if (narrow.addListener) {
			narrow.addListener(sync);
		}
		sync();
	}


	// Coming back to the tile.
	//
	// Add to cart while signed out bounces to /login. Webshop writes the page
	// they were on into localStorage as last_visited and nothing reads it
	// back, so after signing in they landed on the home page with an empty
	// cart and a tile to find again. Frappe's login already honours
	// ?redirect-to=, so this only joins two ends that were already there.
	function comeBackToTheTile() {
		if (location.pathname.split("/")[1] !== "login") {
			return;
		}
		if (location.search.indexOf("redirect-to=") !== -1) {
			return;
		}

		var last = null;
		try {
			last = localStorage.getItem("last_visited");
		} catch (e) {
			return;
		}

		// One leading slash and nothing else: a value starting // is another
		// site, and sending someone off ours after they type a password is
		// exactly the thing not to build.
		if (!last || last.charAt(0) !== "/" || last.charAt(1) === "/") {
			return;
		}
		if (last.split("/")[1] === "login") {
			return;
		}

		try {
			var url = new URL(window.location.href);
			url.searchParams.set("redirect-to", last);
			history.replaceState(null, "", url.toString());
			// Used once. Left lying around it would still be sending people to
			// a tile they looked at weeks ago.
			localStorage.removeItem("last_visited");
		} catch (e) {
			return;
		}

		sayWhyTheyAreHere();
	}

	// The form asks for a password without ever saying why it appeared.
	function sayWhyTheyAreHere() {
		var head = document.querySelector(".aab-login-panel .page-card-head");
		if (!head || document.querySelector(".aab-login-why")) {
			return;
		}
		var p = document.createElement("p");
		p.className = "aab-login-why";
		p.textContent = "Sign in to put this in your cart. We will bring you "
			+ "straight back to it.";
		head.appendChild(p);
	}

	function boot() {
		start();
		startFilters();
		comeBackToTheTile();
	}

	document.addEventListener("DOMContentLoaded", boot);
	window.addEventListener("load", boot);
	if (document.readyState !== "loading") {
		boot();
	}
})();
