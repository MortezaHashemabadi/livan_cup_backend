import io
import json
import pytest
from types import SimpleNamespace
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers as drf_serializers

from accounts.models import User
from .models import Design
from .serializers import DesignSerializer


def make_test_image(name="test.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, "PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.fixture
def user1(db):
    return User.objects.create_user(phone="09121111111")


@pytest.fixture
def user2(db):
    return User.objects.create_user(phone="09122222222")


@pytest.mark.django_db
def test_design_list_returns_only_own_designs(api_client, user1, user2):
    Design.objects.create(user=user1, name="طراحی من", design_data={}, thumbnail=make_test_image())
    Design.objects.create(user=user2, name="طراحی دیگری", design_data={}, thumbnail=make_test_image())

    api_client.force_authenticate(user=user1)
    response = api_client.get("/api/designs/")

    names = [d["name"] for d in response.data]
    assert names == ["طراحی من"]


@pytest.mark.django_db
def test_design_detail_for_other_user_returns_404(api_client, user1, user2):
    other_design = Design.objects.create(user=user2, name="مال دیگری", design_data={}, thumbnail=make_test_image())

    api_client.force_authenticate(user=user1)
    response = api_client.get(f"/api/designs/{other_design.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_design_create_assigns_current_user_and_parses_json(api_client, user1):
    api_client.force_authenticate(user=user1)
    payload = {
        "name": "طراحی جدید",
        "design_data": json.dumps({"shapes": ["circle", "text"]}),
        "thumbnail": make_test_image(),
    }
    response = api_client.post("/api/designs/", payload, format="multipart")

    assert response.status_code == 201
    design = Design.objects.get(id=response.data["id"])
    assert design.user == user1
    assert design.design_data == {"shapes": ["circle", "text"]}  # باید dict باشه، نه رشته


@pytest.mark.django_db
def test_design_update_for_other_user_returns_404(api_client, user1, user2):
    other_design = Design.objects.create(user=user2, name="مال دیگری", design_data={}, thumbnail=make_test_image())

    api_client.force_authenticate(user=user1)
    response = api_client.patch(f"/api/designs/{other_design.id}/", {"name": "تغییر یافته"}, format="json")

    assert response.status_code == 404
    other_design.refresh_from_db()
    assert other_design.name == "مال دیگری"


@pytest.mark.django_db
def test_design_delete_for_other_user_returns_404(api_client, user1, user2):
    other_design = Design.objects.create(user=user2, name="مال دیگری", design_data={}, thumbnail=make_test_image())

    api_client.force_authenticate(user=user1)
    response = api_client.delete(f"/api/designs/{other_design.id}/")

    assert response.status_code == 404
    assert Design.objects.filter(id=other_design.id).exists()


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_designs(api_client):
    response = api_client.get("/api/designs/")
    assert response.status_code == 401


def test_thumbnail_validation_rejects_large_file():
    serializer = DesignSerializer()
    fake_file = SimpleNamespace(size=6 * 1024 * 1024)
    with pytest.raises(drf_serializers.ValidationError):
        serializer.validate_thumbnail(fake_file)


def test_thumbnail_validation_accepts_normal_size_file():
    serializer = DesignSerializer()
    fake_file = SimpleNamespace(size=1 * 1024 * 1024)
    assert serializer.validate_thumbnail(fake_file) is fake_file