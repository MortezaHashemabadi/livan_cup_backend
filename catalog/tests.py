import pytest
from django.core.exceptions import ValidationError

from .models import Category, Attribute, AttributeValue, CategoryAttribute, Product, ProductVariant, ProductImage


@pytest.mark.django_db
def test_category_slug_auto_generated():
    category = Category.objects.create(name="لیوان کاغذی")
    assert category.slug


@pytest.mark.django_db
def test_product_slug_auto_generated():
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان کاغذی ۸ اونسی")
    assert product.slug


@pytest.mark.django_db
def test_single_value_attribute_raises_when_multiple_values_assigned():
    category = Category.objects.create(name="لیوان کاغذی")
    attribute = Attribute.objects.create(name="سایز", slug="size")
    CategoryAttribute.objects.create(category=category, attribute=attribute, allow_multiple_values=False)
    v1 = AttributeValue.objects.create(attribute=attribute, value="8oz")
    v2 = AttributeValue.objects.create(attribute=attribute, value="10oz")
    product = Product.objects.create(category=category, name="لیوان تست")
    variant = ProductVariant.objects.create(product=product, sku="CUP-TEST-1")

    with pytest.raises(ValidationError):
        variant.validate_attribute_combination(attribute_value_ids=[v1.id, v2.id])


@pytest.mark.django_db
def test_multiple_values_allowed_for_accessory_category():
    category = Category.objects.create(name="هولدر", is_accessory=True)
    attribute = Attribute.objects.create(name="سایز", slug="size")
    CategoryAttribute.objects.create(category=category, attribute=attribute, allow_multiple_values=True)
    v1 = AttributeValue.objects.create(attribute=attribute, value="8oz")
    v2 = AttributeValue.objects.create(attribute=attribute, value="10oz")
    product = Product.objects.create(category=category, name="هولدر چندسایز")
    variant = ProductVariant.objects.create(product=product, sku="HOLDER-TEST-1")

    variant.validate_attribute_combination(attribute_value_ids=[v1.id, v2.id])  # نباید خطا بدهد


@pytest.mark.django_db
def test_product_list_returns_only_active_products(api_client):
    category = Category.objects.create(name="لیوان کاغذی")
    Product.objects.create(category=category, name="فعال", is_active=True)
    Product.objects.create(category=category, name="غیرفعال", is_active=False)

    response = api_client.get("/api/catalog/products/")
    names = [p["name"] for p in response.data]  # ← بدون ["results"]

    assert "فعال" in names
    assert "غیرفعال" not in names

@pytest.mark.django_db
def test_product_detail_by_slug(api_client):
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان کاغذی ۸ اونسی")

    response = api_client.get(f"/api/catalog/products/{product.slug}/")
    assert response.status_code == 200
    assert response.data["name"] == "لیوان کاغذی ۸ اونسی"


@pytest.mark.django_db
def test_product_list_filter_by_category(api_client):
    cat1 = Category.objects.create(name="لیوان کاغذی")
    cat2 = Category.objects.create(name="لیوان پلاستیکی شفاف")
    Product.objects.create(category=cat1, name="کاغذی نمونه")
    Product.objects.create(category=cat2, name="پلاستیکی نمونه")

    response = api_client.get(f"/api/catalog/products/?category={cat1.slug}")
    names = [p["name"] for p in response.data]  # ← بدون ["results"]

    assert names == ["کاغذی نمونه"]


@pytest.mark.django_db
def test_compatible_accessories_returns_matching_size_only(api_client):
    size_attr = Attribute.objects.create(name="سایز", slug="size")
    size_8 = AttributeValue.objects.create(attribute=size_attr, value="8oz")
    size_10 = AttributeValue.objects.create(attribute=size_attr, value="10oz")

    cup_category = Category.objects.create(name="لیوان کاغذی")
    holder_category = Category.objects.create(name="هولدر", is_accessory=True)

    cup_product = Product.objects.create(category=cup_category, name="لیوان تست")
    cup_variant = ProductVariant.objects.create(product=cup_product, sku="CUP-8OZ")
    cup_variant.attribute_values.add(size_8)

    holder_product = Product.objects.create(category=holder_category, name="هولدر تست")
    matching_holder = ProductVariant.objects.create(product=holder_product, sku="HOLDER-8OZ")
    matching_holder.attribute_values.add(size_8)
    non_matching_holder = ProductVariant.objects.create(product=holder_product, sku="HOLDER-10OZ")
    non_matching_holder.attribute_values.add(size_10)

    response = api_client.get(f"/api/catalog/variants/{cup_variant.id}/compatible_accessories/")
    skus = [v["sku"] for v in response.data]

    assert "HOLDER-8OZ" in skus
    assert "HOLDER-10OZ" not in skus


@pytest.mark.django_db
def test_only_one_primary_image_per_product():
    category = Category.objects.create(name="لیوان کاغذی")
    product = Product.objects.create(category=category, name="لیوان تست")
    img1 = ProductImage.objects.create(product=product, image="test1.jpg", is_primary=True)
    img2 = ProductImage.objects.create(product=product, image="test2.jpg", is_primary=True)

    img1.refresh_from_db()
    assert img1.is_primary is False
    assert img2.is_primary is True

@pytest.mark.django_db
def test_related_variants_appear_in_product_detail(api_client):
    category = Category.objects.create(name="لیوان کاغذی")
    product1 = Product.objects.create(category=category, name="محصول اصلی")
    product2 = Product.objects.create(category=category, name="محصول مرتبط")
    variant1 = ProductVariant.objects.create(product=product1, sku="MAIN-1")
    variant2 = ProductVariant.objects.create(product=product2, sku="RELATED-1")
    variant1.related_variants.add(variant2)

    response = api_client.get(f"/api/catalog/products/{product1.slug}/")
    variant_data = response.data["variants"][0]
    related_skus = [v["sku"] for v in variant_data["related_variants"]]
    assert related_skus == ["RELATED-1"]

