# استخدام صورة Node.js رسمية كصورة أساسية
# node:18-alpine - صورة خفيفة من Node.js 18
# as build - تسمية المرحلة لاستخدامها لاحقاً
FROM node:18-alpine as build

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات الحزم وتثبيت المكتبات
# يتم نسخ package*.json أولاً لتحسين استخدام طبقات Docker
COPY package*.json ./
RUN npm install

# نسخ باقي كود التطبيق
COPY . .

# بناء تطبيق React
# npm run build - إنشاء نسخة الإنتاج من التطبيق
RUN npm run build

# استخدام خادم ويب خفيف لتقديم الملفات الثابتة
# nginx:alpine - خادم ويب سريع وخفيف
FROM nginx:alpine

# نسخ الملفات المبنية من المرحلة السابقة
# --from=build - نسخ من مرحلة البناء السابقة
# /app/build - مجلد الملفات المبنية
# /usr/share/nginx/html - مجلد الملفات الثابتة في nginx
COPY --from=build /app/build /usr/share/nginx/html

# فتح المنفذ 80 (المنفذ الافتراضي لـ HTTP)
EXPOSE 80

# تشغيل nginx في المقدمة (بدون وضع الخلفية)
CMD ["nginx", "-g", "daemon off;"] 