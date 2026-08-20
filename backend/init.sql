-- تهيئة قاعدة بيانات PostgreSQL لروبوت المحادثة RAG من الصفر
-- هذا السكريبت يحذف جميع الكائنات الموجودة ويعيد إنشاء قاعدة البيانات

-- إنشاء قاعدة البيانات إذا لم تكن موجودة (تشغيل كمسؤول postgres)
-- CREATE DATABASE IF NOT EXISTS rag_db;

-- الاتصال بقاعدة البيانات rag_db
-- \c rag_db;

-- حذف الجداول والكائنات الموجودة (إذا وجدت)
DROP TABLE IF EXISTS course_enrollments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS uploaded_files CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS langchain_pg_embedding CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP INDEX IF EXISTS langchain_pg_embedding_idx;

-- تفعيل إضافة pgvector للبحث الدلالي
CREATE EXTENSION IF NOT EXISTS vector;

-- إنشاء جدول المستخدمين للمصادقة
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'roleenum') THEN
        CREATE TYPE roleenum AS ENUM ('admin', 'faculty', 'student', 'employee', 'general_inquiry');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للمستخدم
    username VARCHAR(255) UNIQUE NOT NULL,  -- اسم المستخدم الفريد
    email VARCHAR(255) UNIQUE NOT NULL,  -- البريد الإلكتروني الفريد
    password_hash VARCHAR(255) NOT NULL,  -- كلمة المرور المشفرة
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- تاريخ إنشاء الحساب
    role roleenum NOT NULL,  -- نوع المستخدم
    specialization VARCHAR(255)  -- التخصص (للطلاب)
);

-- إنشاء جدول رسائل المحادثة لتخزين سجل المحادثات
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للرسالة
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- معرف المستخدم المرسل
    message TEXT NOT NULL,  -- نص الرسالة المرسلة من المستخدم
    response TEXT NOT NULL,  -- رد روبوت المحادثة
    context JSONB,  -- تخزين السياق كـ JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- تاريخ ووقت إرسال الرسالة
);

-- إنشاء جدول الملفات المرفوعة لإدارة الملفات
CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للملف
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- معرف المستخدم الذي رفع الملف
    uploader_id INTEGER REFERENCES users(id) NOT NULL,  -- معرف المستخدم الرافع للملف
    target_roles JSONB NOT NULL,  -- الفئات المستهدفة لهذا الملف
    specialization VARCHAR(255),  -- التخصص المستهدف للملف (للطلاب فقط)
    filename VARCHAR(255) NOT NULL,  -- اسم الملف المحفوظ في النظام
    original_filename VARCHAR(255) NOT NULL,  -- الاسم الأصلي للملف
    file_size INTEGER,  -- حجم الملف بالبايت
    file_type VARCHAR(100),  -- نوع الملف
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- تاريخ ووقت رفع الملف
);

-- إنشاء جدول المجموعات لـ LangChain
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- المعرف الفريد للمجموعة
    name TEXT NOT NULL,  -- اسم المجموعة
    cmetadata JSONB  -- البيانات الوصفية
);

-- إنشاء جدول التضمينات لـ LangChain
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للتضمين
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,  -- معرف المجموعة
    embedding vector(384),  -- المتجه الدلالي (384 بعد)
    document TEXT,  -- النص الأصلي
    cmetadata JSONB,  -- البيانات الوصفية
    custom_id TEXT,  -- معرف مخصص
    uuid UUID DEFAULT gen_random_uuid()  -- معرف فريد للتضمين
);

-- إنشاء فهرس للبحث في المتجهات الدلالية
CREATE INDEX IF NOT EXISTS langchain_pg_embedding_idx ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- إنشاء جدول الوثائق (للتوافق مع الكود الموجود)
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للوثيقة
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- معرف المستخدم
    filename VARCHAR(255) NOT NULL,  -- اسم الملف
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- تاريخ الرفع
    vector vector(1536)  -- المتجه الدلالي (1536 بعد) - تعديل حسب الحاجة
);

-- إنشاء جدول تتبع الملفات المفهرسة
CREATE TABLE IF NOT EXISTS indexed_files_tracking (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للتتبع
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- معرف المستخدم
    file_path TEXT NOT NULL,  -- مسار الملف
    file_hash TEXT NOT NULL,  -- hash فريد للملف
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- تاريخ الفهرسة
    UNIQUE(user_id, file_path)  -- ضمان عدم تكرار الملف لنفس المستخدم
);

-- إنشاء جدول الكورسات التعليمية
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للكورس
    title VARCHAR(255) NOT NULL,  -- عنوان الكورس
    description TEXT,  -- وصف الكورس
    specialization VARCHAR(255) NOT NULL,  -- التخصص المطلوب للكورس
    faculty_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,  -- معرف عضو هيئة التدريس
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- تاريخ إنشاء الكورس
    updated_at TIMESTAMP,  -- تاريخ آخر تحديث
    is_active VARCHAR(10) DEFAULT 'active',  -- حالة الكورس (active/inactive)
    course_url VARCHAR(500),  -- رابط الكورس (داخلي أو خارجي)
    course_type VARCHAR(50) DEFAULT 'internal',  -- نوع الكورس (internal/external)
    thumbnail_url VARCHAR(500)  -- رابط صورة الكورس (thumbnail) - يتم استخراجها تلقائياً من YouTube للكورسات الخارجية
);

-- إضافة عمود thumbnail_url للجداول الموجودة (إذا لم يكن موجوداً)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'courses' AND column_name = 'thumbnail_url'
    ) THEN
        ALTER TABLE courses ADD COLUMN thumbnail_url VARCHAR(500);
    END IF;
END$$;

-- إنشاء جدول تسجيل الطلاب في الكورسات
CREATE TABLE IF NOT EXISTS course_enrollments (
    id SERIAL PRIMARY KEY,  -- المعرف الفريد للتسجيل
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,  -- معرف الطالب
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE NOT NULL,  -- معرف الكورس
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- تاريخ التسجيل
    progress INTEGER DEFAULT 0  -- نسبة الإنجاز من 0 إلى 100
);

-- إضافة عمود specialization للجداول الموجودة (إذا لم يكن موجوداً)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'uploaded_files' AND column_name = 'specialization'
    ) THEN
        ALTER TABLE uploaded_files ADD COLUMN specialization VARCHAR(255);
    END IF;
END$$;

-- إنشاء فهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_upload_time ON uploaded_files(upload_time);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_specialization ON uploaded_files(specialization);
CREATE INDEX IF NOT EXISTS idx_indexed_files_tracking_user_id ON indexed_files_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_indexed_files_tracking_file_path ON indexed_files_tracking(file_path);
CREATE INDEX IF NOT EXISTS idx_courses_faculty_id ON courses(faculty_id);
CREATE INDEX IF NOT EXISTS idx_courses_specialization ON courses(specialization);
CREATE INDEX IF NOT EXISTS idx_courses_created_at ON courses(created_at);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_student_id ON course_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_course_id ON course_enrollments(course_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_course_enrollments_unique ON course_enrollments(student_id, course_id);

-- منح الصلاحيات لمستخدم postgres (بما أننا نستخدم مستخدم postgres)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres; 