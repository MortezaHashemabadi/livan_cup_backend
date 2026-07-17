FROM python:3.12-slim

# جلوگیری از نوشتن .pyc و بافر نشدن output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# نصب dependency های سیستمی (برای psycopg2 اگه بعداً لازم شد، فعلاً حداقلی)
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs staticfiles media

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn cup_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3"]