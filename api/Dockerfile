# استخدام صورة Python رسمية كصورة أساسية
# python:3.10-slim - صورة خفيفة من Python 3.10
FROM python:3.10-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيت المكتبات
# يتم نسخ requirements.txt أولاً لتحسين استخدام طبقات Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي كود التطبيق
COPY . .

# فتح المنفذ الذي يعمل عليه FastAPI
EXPOSE 8000

# الأمر لتشغيل تطبيق FastAPI
# uvicorn - خادم ASGI سريع لتطبيقات Python
# main:app - استيراد كائن app من ملف main.py
# --host 0.0.0.0 - السماح بالاتصال من أي عنوان IP
# --port 8000 - المنفذ الذي سيعمل عليه الخادم
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 