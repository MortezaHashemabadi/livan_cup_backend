from django.core.files.base import ContentFile
from pricing.services import get_unit_price, validate_discount, calculate_discount_amount
from .models import Order, OrderItem


def create_order_from_cart(cart, address, notes=''):
    if not cart.items.exists():
        raise ValueError("سبد خرید خالی است")

    line_data = []
    subtotal = 0
    for item in cart.items.select_related('variant', 'design'):
        unit_price = get_unit_price(item.variant, item.quantity)
        if unit_price is None:
            raise ValueError(f"قیمتی برای تعداد {item.quantity} از {item.variant.sku} ثبت نشده است")
        line_subtotal = unit_price * item.quantity
        subtotal += line_subtotal
        line_data.append((item, unit_price, line_subtotal))

    discount_amount = 0
    if cart.discount:
        validate_discount(cart.discount, subtotal)  # ValueError می‌دهد اگر نامعتبر باشد
        discount_amount = calculate_discount_amount(cart.discount, subtotal)

    order = Order.objects.create(
        user=cart.user,
        address=address,
        address_snapshot=f"{address.province}، {address.city}، {address.full_address}",
        discount=cart.discount,
        discount_amount=discount_amount,
        subtotal=subtotal,
        total=subtotal - discount_amount,
        notes=notes,
    )


    for item, unit_price, line_subtotal in line_data:
        order_item = OrderItem(
            order=order, variant=item.variant, design=item.design,
            quantity=item.quantity, unit_price=unit_price, subtotal=line_subtotal,
        )
        order_item.save()  # اول save کن تا ID بگیره

        if item.print_file:
            try:
                item.print_file.open('rb')
                order_item.print_file.save(
                    item.print_file.name.split('/')[-1],
                    ContentFile(item.print_file.read()),
                    save=True,  # ← اینجا True بشه تا مطمئن بشیم ذخیره شد
                )
            finally:
                item.print_file.close()

    if cart.discount:
        cart.discount.used_count += 1
        cart.discount.save(update_fields=['used_count'])

    cart.items.all().delete()
    cart.discount = None
    cart.save(update_fields=['discount'])

    return order