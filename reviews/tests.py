import pytest

from accounts.models import User, Address
from catalog.models import Category, Product, ProductVariant
from cart_orders.models import Order, OrderItem
from .models import ProductReview, Testimonial


@pytest.fixture
def user1(db):
    return User.objects.create_user(phone="09121111111")


@pytest.fixture
def user2(db):
    return User.objects.create_user(phone="09122222222")


@pytest.fixture
def address1(db, user1):
    return Address.objects.create(user=user1, province="تهران", city="تهران", full_address="خیابان آزادی")


@pytest.fixture
def product(db):
    category = Category.objects.create(name="لیوان کاغذی")
    return Product.objects.create(category=category, name="لیوان تست")


@pytest.fixture
def variant(db, product):
    return ProductVariant.objects.create(product=product, sku="CUP-REVIEW-1")


def make_order_with_item(user, address, variant, status='pending'):
    order = Order.objects.create(
        user=user, address=address, address_snapshot="آدرس تست",
        subtotal=10000, total=10000, status=status,
    )
    OrderItem.objects.create(order=order, variant=variant, quantity=5, unit_price=2000, subtotal=10000)
    return order


# ---------- کنترل دسترسی ثبت نظر ----------

@pytest.mark.django_db
def test_cannot_review_without_purchase(api_client, user1, product):
    api_client.force_authenticate(user=user1)
    response = api_client.post(
        "/api/reviews/product-reviews/", {"product": product.id, "rating": 5, "comment": "خوب بود"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_can_review_after_purchase(api_client, user1, address1, product, variant):
    make_order_with_item(user1, address1, variant)
    api_client.force_authenticate(user=user1)
    response = api_client.post(
        "/api/reviews/product-reviews/", {"product": product.id, "rating": 5, "comment": "عالی بود"}, format="json"
    )
    assert response.status_code == 201
    review = ProductReview.objects.get(product=product, user=user1)
    assert review.is_approved is False  # پیش‌فرض تاییدنشده


@pytest.mark.django_db
def test_purchase_check_excludes_cancelled_orders(api_client, user1, address1, product, variant):
    make_order_with_item(user1, address1, variant, status='cancelled')
    api_client.force_authenticate(user=user1)
    response = api_client.post(
        "/api/reviews/product-reviews/", {"product": product.id, "rating": 5, "comment": "تست"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_cannot_review_same_product_twice(api_client, user1, address1, product, variant):
    make_order_with_item(user1, address1, variant)
    api_client.force_authenticate(user=user1)
    api_client.post("/api/reviews/product-reviews/", {"product": product.id, "rating": 4, "comment": "خوب"}, format="json")

    response = api_client.post(
        "/api/reviews/product-reviews/", {"product": product.id, "rating": 5, "comment": "دوباره"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_review_create_requires_auth(api_client, product):
    response = api_client.post(
        "/api/reviews/product-reviews/", {"product": product.id, "rating": 5, "comment": "..."}, format="json"
    )
    assert response.status_code == 401


# ---------- نمایش عمومی فقط تایید شده‌ها ----------

@pytest.mark.django_db
def test_unapproved_review_not_in_public_list(api_client, user1, address1, product, variant):
    make_order_with_item(user1, address1, variant)
    ProductReview.objects.create(product=product, user=user1, rating=5, comment="تاییدنشده", is_approved=False)

    response = api_client.get(f"/api/reviews/product-reviews/?product={product.id}")
    assert response.data == []


@pytest.mark.django_db
def test_approved_review_appears_in_public_list(api_client, user1, address1, product, variant):
    make_order_with_item(user1, address1, variant)
    ProductReview.objects.create(product=product, user=user1, rating=5, comment="تاییدشده", is_approved=True)

    response = api_client.get(f"/api/reviews/product-reviews/?product={product.id}")
    assert len(response.data) == 1
    assert response.data[0]["comment"] == "تاییدشده"


@pytest.mark.django_db
def test_review_list_filters_by_product(api_client, user1, user2, address1, product, variant):
    category2 = Category.objects.create(name="لیوان پلاستیکی")
    product2 = Product.objects.create(category=category2, name="لیوان تست ۲")
    variant2 = ProductVariant.objects.create(product=product2, sku="CUP-REVIEW-2")
    address2 = Address.objects.create(user=user2, province="تهران", city="تهران", full_address="آزادی ۲")

    make_order_with_item(user1, address1, variant)
    make_order_with_item(user2, address2, variant2)
    ProductReview.objects.create(product=product, user=user1, rating=5, comment="نظر محصول ۱", is_approved=True)
    ProductReview.objects.create(product=product2, user=user2, rating=4, comment="نظر محصول ۲", is_approved=True)

    response = api_client.get(f"/api/reviews/product-reviews/?product={product.id}")
    comments = [r["comment"] for r in response.data]
    assert comments == ["نظر محصول ۱"]


# ---------- Testimonial ----------

@pytest.mark.django_db
def test_testimonial_list_only_featured(api_client):
    Testimonial.objects.create(customer_name="کافه آرامیس", comment="عالی بود", is_featured=True)
    Testimonial.objects.create(customer_name="رستوران تست", comment="مخفی", is_featured=False)

    response = api_client.get("/api/reviews/testimonials/")
    names = [t["customer_name"] for t in response.data]
    assert names == ["کافه آرامیس"]