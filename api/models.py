from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum as PyEnum

# تعريف دور المستخدم كـ Enum مركزي
class RoleEnum(str, PyEnum):
    faculty = "faculty"
    student = "student"
    admin = "admin"

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: RoleEnum
    specialization: Optional[str] = None  # التخصص (للطلاب)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    role: RoleEnum
    specialization: Optional[str] = None
    university_id: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

class AdminUserListItem(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum
    university_id: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AdminUserListResponse(BaseModel):
    users: List[AdminUserListItem]
    total: int
    page: int
    page_size: int

class AdminUserSummaryResponse(BaseModel):
    total: int
    students: int
    faculty: int
    admins: int

class AdminUploadUsersResponse(BaseModel):
    added: int
    skipped: int
    errors: List[dict]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChatMessageRequest(BaseModel):
    message: str
    top_k: Optional[int] = 3
    temperature: Optional[float] = 0.2
    output_length: Optional[str] = "mid"
    enable_web_search: Optional[bool] = False
    course_id: Optional[int] = None

class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    message: str
    response: str
    context: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]

class FileUploadResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    specialization: Optional[str] = None
    course_id: Optional[int] = None
    course_ids: Optional[List[int]] = None
    level: Optional[str] = None
    upload_time: datetime

    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileUploadResponse]

class ChatResponse(BaseModel):
    answer: str
    context: List[str]

class DocumentUploadResponse(BaseModel):
    message: str
    documents_processed: int
    total_chunks: int
    total_documents: int

class IndexStats(BaseModel):
    total_documents: int
    total_chunks: int
    vector_store_available: bool
    llm_available: bool
    database: str
    llm: str

# نماذج الكورسات
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    specialization: str
    level: Optional[str] = None
    course_code: Optional[str] = None
    course_url: Optional[str] = None
    course_type: Optional[str] = "internal"  # internal, external
    thumbnail_url: Optional[str] = None  # Will be auto-generated for YouTube URLs

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    specialization: Optional[str] = None
    level: Optional[str] = None
    course_code: Optional[str] = None
    course_url: Optional[str] = None
    is_active: Optional[str] = None
    course_type: Optional[str] = None
    thumbnail_url: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    specialization: str
    level: Optional[str] = None
    course_code: Optional[str] = None
    faculty_id: int
    faculty_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: str
    course_url: Optional[str]
    course_type: str
    thumbnail_url: Optional[str] = None
    enrollment_count: Optional[int] = 0
    credit_hours: Optional[int] = None

    class Config:
        from_attributes = True


class CatalogLevelResponse(BaseModel):
    id: str
    label_ar: str
    label_en: str


class CatalogCourseResponse(BaseModel):
    code: str
    title: str
    level: str
    credit_hours: int
    specialization: str


class CatalogLevelsResponse(BaseModel):
    levels: List[CatalogLevelResponse]


class CatalogCoursesResponse(BaseModel):
    level: str
    courses: List[CatalogCourseResponse]

class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    total: int

class CourseEnrollmentRequest(BaseModel):
    course_id: int

class CourseEnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime
    progress: int
    section_number: Optional[str] = None
    level: Optional[str] = None
    student_name: Optional[str] = None
    university_id: Optional[str] = None
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True


class CourseRosterUploadResponse(BaseModel):
    linked: int
    skipped: int
    errors: List[dict]
    reindexed_students: int = 0


class FacultyStudentsUploadResponse(BaseModel):
    linked: int
    skipped: int
    errors: List[dict]
    reindexed_students: int = 0