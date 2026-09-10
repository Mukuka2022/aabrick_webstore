/* Enquiry form.
 *
 * Pure ASCII: served without a charset.
 *
 * Posts to our own whitelisted method rather than submitting the form, so the
 * customer stays on the page and gets a reference back. The button is disabled
 * while it is in flight, because a double tap on a slow connection would
 * otherwise raise two leads for one enquiry.
 */
(function () {
	"use strict";

	function $(id) {
		return document.getElementById(id);
	}

	function say(text, kind) {
		var msg = $("fMsg");
		msg.textContent = text;
		msg.className = "aab-enquiry-msg" + (kind ? " is-" + kind : "");
	}

	function send(e) {
		e.preventDefault();

		var name = $("fName").value.trim();
		var phone = $("fPhone").value.trim();

		if (!name) {
			say("Please tell us your name.", "bad");
			$("fName").focus();
			return;
		}
		if (!phone) {
			say("Please give us a phone number so we can reply.", "bad");
			$("fPhone").focus();
			return;
		}

		var btn = $("fSend");
		btn.disabled = true;
		say("Sending...");

		frappe.call({
			method: "aabrick_webstore.enquiry.submit",
			type: "POST",
			args: {
				name: name,
				phone: phone,
				email: $("fEmail").value.trim(),
				branch: $("fBranch").value,
				message: $("fMessage").value.trim(),
				item_code: $("fItem").value,
				quantity: $("fQty").value,
				area: $("fArea").value
			},
			callback: function (r) {
				btn.disabled = false;
				if (r && r.message && r.message.ok) {
					$("aab-enquiry").reset();
					say("Thank you. We have it, and someone will call you. Your reference is "
						+ r.message.reference + ".", "good");
				} else {
					say("Something went wrong. Please call us on the number beside this form.", "bad");
				}
			},
			error: function () {
				btn.disabled = false;
				say("Something went wrong. Please call us on the number beside this form.", "bad");
			}
		});
	}

	function start() {
		var form = $("aab-enquiry");
		if (!form || form.__aabBound) {
			return;
		}
		form.__aabBound = true;
		form.addEventListener("submit", send);
	}

	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
