"""Sign up, without showing a customer the inside of the server.

When the welcome mail cannot be sent, frappe's sign_up lets the exception
out, and the customer gets a dialog reading

    Failed to decrypt key Email Account.AABrick.password
    Encryption key is invalid! Please check site_config.json

under a button that says OOPS! SOMETHING WENT WRONG. That is a stranger
being handed the name of a config file and told to check it. Whatever is
wrong on the server, this is not the place it gets reported.

So the real failure goes to the Error Log where somebody at AABrick will
find it, and the customer is told plainly that it did not work and given
the sales line, which is a thing they can actually act on.

Nothing here changes when sign up succeeds: frappe's own function does the
work and its answer is passed straight back.
"""

import frappe
from frappe import _

PHONE = "+260 960 787 777"


@frappe.whitelist(allow_guest=True)
def sign_up(email: str, full_name: str, redirect_to: str) -> tuple[int, str]:
    from frappe.core.doctype.user.user import sign_up as frappe_sign_up

    try:
        return frappe_sign_up(email, full_name, redirect_to)
    except Exception:
        # Everything, deliberately. The first version let ValidationError
        # through on the grounds that frappe's own refusals use it, and the
        # decrypt failure is a ValidationError, so the one error this exists
        # for was the one that got past. The only deliberate throw in
        # sign_up is "Sign Up is disabled", and the sales line is a fine
        # answer to that too.
        # The account, if one was made, goes with the failure: an account
        # whose welcome mail never arrived cannot be signed into anyway,
        # and left behind it answers the next attempt with "Already
        # Registered", so the customer cannot even start again.
        frappe.db.rollback()
        _remove_half_made_account(email)
        frappe.log_error(
            title="Website sign up failed",
            message=frappe.get_traceback(with_context=True),
        )
        # Whatever the server wanted to say about itself, stop it here.
        frappe.local.message_log = []
        if hasattr(frappe, "clear_last_message"):
            frappe.clear_last_message()

        return 0, _(
            "We could not finish setting up your account just now. "
            "Please call us on {0} and we will take your order over the phone."
        ).format(PHONE)


def _remove_half_made_account(email):
    """Delete the account this call just made, if it made one.

    Deliberately narrow. It must be a website user, self registered,
    never signed into, and made in the last few minutes. Anything else is
    somebody's real account and is left alone.
    """
    try:
        user = frappe.db.get_value(
            "User",
            {"name": email},
            ["name", "user_type", "owner", "last_login", "creation"],
            as_dict=True,
        )
        if not user:
            return
        if user.user_type != "Website User" or user.owner != "Guest":
            return
        if user.last_login:
            return
        age = frappe.utils.time_diff_in_seconds(
            frappe.utils.now_datetime(), user.creation)
        if age > 300:
            return

        for contact in frappe.get_all("Contact", filters={"user": email},
                                      pluck="name"):
            frappe.delete_doc("Contact", contact, force=True,
                              ignore_permissions=True)
        frappe.delete_doc("User", email, force=True, ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        # Tidying up is not worth a second failure on top of the first.
        frappe.log_error(title="Could not remove a half made account")
