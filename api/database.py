from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SqlEnum, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import JSONB
from pathlib import Path
from sqlalchemy import text

# Load api/.env regardless of the process working directory
load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("PGVECTOR_CONNECTION_STRING")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL or PGVECTOR_CONNECTION_STRING must be set")

# Neon (and other serverless Postgres) closes idle SSL connections.
# pool_pre_ping detects dead sockets; pool_recycle replaces them before timeout.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RoleEnum(str, PyEnum):
    faculty = "faculty"
    student = "student"
    admin = "admin"

ADMIN_EMAIL = "eng-maha@gmail.com"
ADMIN_USERNAME = "maha"
ADMIN_DEFAULT_PASSWORD = "maha1234"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(SqlEnum(RoleEnum), nullable=False)
    specialization = Column(String(255), nullable=True)  # التخصص للطلاب
    university_id = Column(String(64), unique=True, index=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)
    level = Column(String(64), nullable=True, index=True)  # academic level from faculty roster

    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    uploaded_files = relationship(
        "UploadedFile",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UploadedFile.user_id"
    )  # الملفات المرفوعة
    created_courses = relationship("Course", back_populates="faculty", cascade="all, delete-orphan")
    enrollments = relationship("CourseEnrollment", back_populates="student", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_roles = Column(JSONB, nullable=False)
    specialization = Column(String(255), nullable=True)  # التخصص المستهدف للملف (للطلاب فقط)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    course_ids = Column(JSONB, nullable=True)  # multi-course attach for student materials
    level = Column(String(64), nullable=True, index=True)  # level selected at upload
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(100))
    # Persist bytes in Neon so downloads survive Render ephemeral disk resets
    file_content = Column(LargeBinary, nullable=True)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship(
        "User",
        back_populates="uploaded_files",
        foreign_keys=[user_id]
    )
    uploader = relationship(
        "User",
        foreign_keys=[uploader_id]
    )

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    specialization = Column(String(255), nullable=False, index=True)  # التخصص المطلوب للكورس
    level = Column(String(64), nullable=True, index=True)  # e.g. "1", "2"
    course_code = Column(String(64), nullable=True, index=True)  # e.g. "2310 ويب"
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(String(10), default="active")  # active, inactive
    course_url = Column(String(500), nullable=True)  # رابط الكورس (داخلي أو خارجي)
    course_type = Column(String(50), default="internal")  # internal, external
    thumbnail_url = Column(String(500), nullable=True)  # رابط صورة الكورس (thumbnail)

    faculty = relationship("User", back_populates="created_courses")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    section_number = Column(String(64), nullable=True)
    level = Column(String(64), nullable=True, index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)  # نسبة الإنجاز من 0 إلى 100

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

def ensure_system_users(db):
    """
    Always ensure the sole Administrative account (Maha) exists and is synced.
    Runs on every API startup — creates or repairs eng-maha@gmail.com / maha.
    """
    try:
        from auth import get_password_hash
    except ImportError:
        from api.auth import get_password_hash

    admin_password = os.getenv("ADMIN_PASSWORD", ADMIN_DEFAULT_PASSWORD)
    password_hash = get_password_hash(admin_password)

    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if not existing:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()

    if existing:
        existing.email = ADMIN_EMAIL
        existing.username = ADMIN_USERNAME
        existing.role = RoleEnum.admin
        existing.password_hash = password_hash
        if not existing.display_name:
            existing.display_name = "MANAMU Administrator"
        db.commit()
        print(f"Administrative account ready: {ADMIN_EMAIL} / {ADMIN_USERNAME}")
        return existing

    # Demote any other admin rows so Maha is the sole admin identity
    for other in db.query(User).filter(User.role == RoleEnum.admin).all():
        other.role = RoleEnum.faculty
        print(f"Demoted non-Maha admin to faculty: {other.email}")

    admin_user = User(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password_hash=password_hash,
        role=RoleEnum.admin,
        display_name="MANAMU Administrator",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"Seeded administrative account: {ADMIN_EMAIL}")
    return admin_user


def clear_application_data(db, keep_admin: bool = True):
    """
    Wipe app tables (users/courses/files/chat/enrollments) and optional RAG tables.
    Always re-seeds Maha afterwards when keep_admin=True.
    """
    # Order matters for FKs — use TRUNCATE CASCADE where possible
    with engine.begin() as conn:
        for table in (
            "chat_messages",
            "course_enrollments",
            "uploaded_files",
            "courses",
            "users",
        ):
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        # Vector store (if present)
        conn.execute(text("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS langchain_pg_collection CASCADE"))
    print("Cleared application database tables")
    if keep_admin:
        return ensure_system_users(db)
    return None


def create_tables():
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_content BYTEA"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS university_id VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(255)"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(32)"
            ))
            conn.execute(text(
                "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS course_id INTEGER"
            ))
            conn.execute(text(
                "ALTER TABLE course_enrollments ADD COLUMN IF NOT EXISTS section_number VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS level VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE courses ADD COLUMN IF NOT EXISTS level VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE course_enrollments ADD COLUMN IF NOT EXISTS level VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS course_ids JSONB"
            ))
            conn.execute(text(
                "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS level VARCHAR(64)"
            ))
            conn.execute(text(
                "ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_code VARCHAR(64)"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_university_id "
                "ON users (university_id) WHERE university_id IS NOT NULL"
            ))
            # Remove legacy courses with no level — Learning Platform requires level
            conn.execute(text(
                "DELETE FROM course_enrollments WHERE course_id IN "
                "(SELECT id FROM courses WHERE level IS NULL)"
            ))
            conn.execute(text(
                "DELETE FROM courses WHERE level IS NULL"
            ))
            # Postgres enum migration for admin role
            conn.execute(text(
                "DO $$ BEGIN "
                "ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'admin'; "
                "EXCEPTION WHEN duplicate_object THEN NULL; "
                "END $$;"
            ))
    except Exception as e:
        print(f"⚠️ Schema migration warning: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()