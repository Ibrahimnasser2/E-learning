from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import JSONB
from pathlib import Path

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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(SqlEnum(RoleEnum), nullable=False)
    specialization = Column(String(255), nullable=True)  # التخصص للطلاب

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
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(100))
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
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)  # نسبة الإنجاز من 0 إلى 100

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

def ensure_system_users(db):
    """Create system users if they don't exist"""
    # No longer need system users since we removed general_inquiry
    return None

def create_tables():
    Base.metadata.create_all(bind=engine)
    # No longer need to create system users

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()