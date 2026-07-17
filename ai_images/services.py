import requests
import base64 as b64lib
from django.conf import settings
from django.core.files.base import ContentFile
from .models import ImageGenerationQuota


class ImageGenerationError(Exception):
    pass


class QuotaExceededError(Exception):
    pass



def _call_bridge(prompt: str, existing_image_urls: list, logo_file=None, reference_files=None) -> str:
    payload = {
        "prompt": prompt,
        "existing_image_urls": existing_image_urls or [],
    }

    if logo_file:
        logo_file.seek(0)
        ct = getattr(logo_file, 'content_type', 'image/png')
        encoded = b64lib.b64encode(logo_file.read()).decode('utf-8')
        payload["logo_base64"] = f"data:{ct};base64,{encoded}"

    if reference_files:
        refs = []
        for rf in reference_files:
            rf.seek(0)
            ct = getattr(rf, 'content_type', 'image/png')
            encoded = b64lib.b64encode(rf.read()).decode('utf-8')
            refs.append(f"data:{ct};base64,{encoded}")
        payload["reference_base64"] = refs

    try:
        response = requests.post(
            f"{settings.BASE44_BRIDGE_URL}/generate-image",
            json=payload,
            headers={"x-internal-secret": settings.BASE44_BRIDGE_SECRET},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        raise ImageGenerationError("سرویس تولید تصویر در زمان مقرر پاسخ نداد")
    except requests.RequestException as e:
        raise ImageGenerationError(f"خطا در اتصال به سرویس تولید تصویر: {e}")

    url = data.get("url")
    if not url:
        raise ImageGenerationError("پاسخ سرویس تصویر معتبر نیست")
    return url


def generate_image(prompt: str, user, existing_image_urls: list = None, logo_file=None, reference_files=None) -> str:
    quota = ImageGenerationQuota.get_or_reset(user)
    if not quota.has_remaining():
        raise QuotaExceededError(
            f"سقف ماهانه‌ی تولید تصویر ({ImageGenerationQuota.MONTHLY_LIMIT} عدد) به پایان رسیده است. "
            f"از ماه آینده مجدداً فعال می‌شود."
        )
    url = _call_bridge(prompt, existing_image_urls or [], logo_file=logo_file, reference_files=reference_files)
    stored_url = _download_and_store(url, prompt)
    quota.increment()
    return stored_url


def _download_and_store(image_url: str, prompt: str) -> str:
    try:
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ImageGenerationError(f"دانلود تصویر تولیدشده ناموفق بود: {e}")

    from .models import GeneratedImage
    import hashlib, time
    filename = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:12] + ".png"

    instance = GeneratedImage()
    instance.prompt = prompt
    instance.image.save(filename, ContentFile(resp.content), save=True)
    return instance.image.url