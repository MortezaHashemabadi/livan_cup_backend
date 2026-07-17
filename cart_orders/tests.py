import io
import pytest
from datetime import timedelta
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from accounts.models import User, Address
from catalog.models import Category, Product, ProductVariant, StockStatus
from pricing.models import PriceTier, Discount, DiscountType
from designs.models import Design
from .models import Cart, CartItem, Order


def make_test_image(name="test.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buffer, "PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.fixture
def user1(db):
    return User.objects.create_user(phone="09121111111")


@pytest.fixture
def user2(db):
    return User.objects.create_user(phone="09122222222")


@pytest.fixture
def address1(db, user1):
    return Address.objects.create(
        user=user1, province="تهران", city="تهران", full_address="خیابان آزادی", is_default=True
    )


@pytest.fixture
def variant_with_tiers(db):
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان تست")
    variant = ProductVariant.objects.create(product=product, sku="CUP-TEST-1", stock_status=StockStatus.IN_STOCK)
    PriceTier.objects.create(variant=variant, min_quantity=1, max_quantity=99, unit_price=2000)
    PriceTier.objects.create(variant=variant, min_quantity=100, max_quantity=None, unit_price=1500)
    return variant


@pytest.fixture
def out_of_stock_variant(db):
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان ناموجود")
    return ProductVariant.objects.create(product=product, sku="CUP-OOS-1", stock_status=StockStatus.OUT_OF_STOCK)


@pytest.fixture
def design1(db, user1):
    return Design.objects.create(user=user1, name="طراحی من", design_data={}, thumbnail=make_test_image())


@pytest.fixture
def design2(db, user2):
    return Design.objects.create(user=user2, name="طراحی دیگری", design_data={}, thumbnail=make_test_image())


# ---------- جلوگیری از حالت‌های نامعتبر ----------

@pytest.mark.django_db
def test_cannot_add_out_of_stock_variant_to_cart(api_client, user1, out_of_stock_variant):
    api_client.force_authenticate(user=user1)
    response = api_client.post(
        "/api/cart/items/", {"variant": out_of_stock_variant.id, "quantity": 5}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_cannot_use_other_users_design(api_client, user1, variant_with_tiers, design2):
    api_client.force_authenticate(user=user1)
    response = api_client.post(
        "/api/cart/items/",
        {"variant": variant_with_tiers.id, "design": design2.id, "quantity": 1},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_cannot_access_cart(api_client):
    response = api_client.get("/api/cart/")
    assert response.status_code == 401


# ---------- منطق سبد خرید ----------

@pytest.mark.django_db
def test_adding_same_variant_increases_quantity_instead_of_new_row(api_client, user1, variant_with_tiers):
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 5}, format="json")
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 3}, format="json")

    cart = Cart.objects.get(user=user1)
    assert cart.items.count() == 1
    assert cart.items.first().quantity == 8


@pytest.mark.django_db
def test_cart_subtotal_uses_correct_price_tier(api_client, user1, variant_with_tiers):
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 150}, format="json")

    response = api_client.get("/api/cart/")
    assert response.data["subtotal"] == 150 * 1500  # تایر بالای ۱۰۰ واحد


# ---------- تخفیف ----------

@pytest.mark.django_db
def test_apply_discount_reduces_cart_total(api_client, user1, variant_with_tiers):
    Discount.objects.create(
        name="ده درصد", code="TEN10", discount_type=DiscountType.PERCENTAGE, value=10,
        valid_from=timezone.now() - timedelta(days=1), valid_to=timezone.now() + timedelta(days=1),
    )
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 10}, format="json")
    response = api_client.post("/api/cart/apply-discount/", {"code": "TEN10"}, format="json")

    assert response.status_code == 200
    assert response.data["discount_amount"] == 2000  # ۱۰٪ از ۲۰۰۰۰
    assert response.data["total"] == 18000


@pytest.mark.django_db
def test_apply_discount_fails_when_min_order_not_met(api_client, user1, variant_with_tiers):
    Discount.objects.create(
        name="تخفیف با حداقل سفارش", code="MIN100K", discount_type=DiscountType.FIXED, value=5000,
        min_order_amount=100000,
        valid_from=timezone.now() - timedelta(days=1), valid_to=timezone.now() + timedelta(days=1),
    )
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 5}, format="json")  # subtotal=10000

    response = api_client.post("/api/cart/apply-discount/", {"code": "MIN100K"}, format="json")
    assert response.status_code == 400


# ---------- Checkout ----------

@pytest.mark.django_db
def test_checkout_empty_cart_fails(api_client, user1, address1):
    api_client.force_authenticate(user=user1)
    response = api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_checkout_fails_when_quantity_has_no_matching_tier(api_client, user1, address1):
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان محدود")
    variant = ProductVariant.objects.create(product=product, sku="CUP-LIMITED-1")
    PriceTier.objects.create(variant=variant, min_quantity=1, max_quantity=50, unit_price=2000)

    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant.id, "quantity": 200}, format="json")

    response = api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_checkout_freezes_unit_price_at_purchase_time(api_client, user1, address1, variant_with_tiers):
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 10}, format="json")

    response = api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")
    assert response.status_code == 201

    order = Order.objects.get(user=user1)
    order_item = order.items.first()
    assert order_item.unit_price == 2000
    assert order_item.subtotal == 20000

    # تغییر قیمت بعد از سفارش نباید روی سفارش قبلی اثر بگذارد
    tier = variant_with_tiers.price_tiers.get(min_quantity=1)
    tier.unit_price = 9999
    tier.save()

    order_item.refresh_from_db()
    assert order_item.unit_price == 2000


@pytest.mark.django_db
def test_checkout_copies_print_file_to_order_item(api_client, user1, address1, variant_with_tiers):
    cart = Cart.objects.create(user=user1)
    CartItem.objects.create(
        cart=cart, variant=variant_with_tiers, quantity=5, print_file=make_test_image("cart_print.png")
    )

    api_client.force_authenticate(user=user1)
    response = api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")
    assert response.status_code == 201

    order = Order.objects.get(user=user1)
    order_item = order.items.first()
    assert order_item.print_file
    assert "order_print_files" in order_item.print_file.name  # یعنی کپی جدا شده، نه همون مسیر سبد


@pytest.mark.django_db
def test_checkout_clears_cart_and_increments_discount_usage(api_client, user1, address1, variant_with_tiers):
    discount = Discount.objects.create(
        name="ده درصد", code="TEN10", discount_type=DiscountType.PERCENTAGE, value=10,
        valid_from=timezone.now() - timedelta(days=1), valid_to=timezone.now() + timedelta(days=1),
        used_count=0,
    )
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 10}, format="json")
    api_client.post("/api/cart/apply-discount/", {"code": "TEN10"}, format="json")

    response = api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")
    assert response.status_code == 201

    discount.refresh_from_db()
    assert discount.used_count == 1

    cart = Cart.objects.get(user=user1)
    assert cart.items.count() == 0
    assert cart.discount is None


@pytest.mark.django_db
def test_order_list_only_returns_own_orders(api_client, user1, user2, address1, variant_with_tiers):
    api_client.force_authenticate(user=user1)
    api_client.post("/api/cart/items/", {"variant": variant_with_tiers.id, "quantity": 5}, format="json")
    api_client.post("/api/cart/checkout/", {"address_id": address1.id}, format="json")

    api_client.force_authenticate(user=user2)
    response = api_client.get("/api/orders/")
    assert response.data == []