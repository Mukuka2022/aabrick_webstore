"""Taking the last thing out of the cart should not throw.

webshop's update_cart ends like this:

    if not empty_card:
        quotation.save()
    else:
        quotation.delete()
        quotation = None

    set_cart_count(quotation)

    if cint(with_items):
        ...
    else:
        return {"name": quotation.name}

When the last line goes, the quotation is deleted, the local name is set
to None, and then .name is read off it. The work is already done and
committed by then; only the answer is broken. The customer sees an error
for an action that in fact succeeded, which is the worst shape of bug,
because the obvious response is to try it again.

Registered through override_whitelisted_methods, so every caller reaches
this instead, and webshop is left untouched and upgradeable.
"""

import frappe


@frappe.whitelist()
def update_cart(item_code, qty, additional_notes=None, with_items=False):
    from webshop.webshop.shopping_cart.cart import update_cart as webshop_update_cart

    try:
        return webshop_update_cart(item_code, qty, additional_notes, with_items)
    except AttributeError as e:
        # Narrow on purpose. Any other AttributeError is a real fault and
        # should carry on being one.
        if "'NoneType' object has no attribute 'name'" not in str(e):
            raise
        # The cart is gone because it is empty, which is what was asked for.
        return {"name": None}
