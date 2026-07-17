import io
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import GalleryImage


def make_test_image(name="gallery.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="green").save(buffer, "PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.django_db
def test_gallery_list_only_featured(api_client):
    GalleryImage.objects.create(image=make_test_image(), title="فیچرد", is_featured=True)
    GalleryImage.objects.create(image=make_test_image(), title="مخفی", is_featured=False)

    response = api_client.get("/api/gallery/")
    titles = [g["title"] for g in response.data]
    assert titles == ["فیچرد"]


@pytest.mark.django_db
def test_gallery_filter_by_tag(api_client):
    GalleryImage.objects.create(image=make_test_image(), title="کافه‌ای", tag="کافه")
    GalleryImage.objects.create(image=make_test_image(), title="فست‌فودی", tag="فست‌فود")

    response = api_client.get("/api/gallery/?tag=کافه")
    titles = [g["title"] for g in response.data]
    assert titles == ["کافه‌ای"]