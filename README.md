# LivanCup Backend

بک‌اند Django REST Framework برای [iranlivan.ir](https://iranlivan.ir) — فروشگاه آنلاین لیوان و ظروف قابل سفارشی‌سازی با طراحی هوش مصنوعی.

## ویژگی‌ها

- احراز هویت با شماره موبایل (OTP) + JWT
- کاتالوگ محصولات با ویژگی‌های داینامیک (Attribute-based variants)
- قیمت‌گذاری پلکانی و کد تخفیف
- طراحی سفارشی با Konva.js (جدا از محصولات)
- سبد خرید و مدیریت سفارش
- نظرات کاربران (با تایید خرید واقعی)
- گالری طرح‌ها
- سیستم تیکت پشتیبانی
- تولید تصویر با هوش مصنوعی (از طریق Base44 bridge)
- Rate limiting برای OTP و درخواست‌های عمومی/کاربر (throttling)
- تنظیمات امنیتی پروداکشن (HSTS, SSL redirect, secure cookies, CORS/CSRF محدود)
- معماری decoupled برای طراحی سفارشی (Design جدا از Product، قابل استفاده در محصولات مختلف)

## تکنولوژی‌ها

- Django 5 + Django REST Framework
- JWT (djangorestframework-simplejwt) + Phone OTP
- SQLite (persistent volume)
- WhiteNoise
- pytest + pytest-django + factory_boy

## ساختار پروژه

```
cup_backend/
├── accounts/       # احراز هویت، کاربران، آدرس‌ها
├── catalog/        # محصولات و ویژگی‌ها
├── pricing/        # قیمت‌گذاری و تخفیف
├── designs/        # طرح‌های سفارشی (Konva JSON)
├── cart_orders/    # سبد خرید و سفارش
├── reviews/        # نظرات کاربران
├── gallery/        # گالری طرح‌ها
├── tickets/        # تیکت پشتیبانی
├── ai_images/      # تولید تصویر با AI
└── cup_backend/    # تنظیمات اصلی پروژه
```

## راه‌اندازی

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## تست

```bash
pip install -r requirements-dev.txt
pytest
pytest --cov=. --cov-report=term-missing
```

## Environment Variables

| متغیر | توضیح |
|---|---|
| `SECRET_KEY` | کلید امنیتی Django |
| `DEBUG` | `False` در پروداکشن |
| `ALLOWED_HOSTS` | دامنه‌های مجاز، جدا با کاما |
| `DATABASE_URL` | آدرس دیتابیس (پیش‌فرض SQLite) |
| `SMS_PROVIDER` | `console` یا `kavenegar` |
| `BASE44_BRIDGE_URL` | آدرس سرویس bridge برای AI image |

## Deployment

با Docker اجرا می‌شه. `Dockerfile` شامل gunicorn + collectstatic + migrate خودکاره.

## لایسنس

Private / Proprietary
