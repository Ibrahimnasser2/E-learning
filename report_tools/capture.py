"""Capture screenshots of every page in the MANAMU app using Playwright.

The frontend is expected to be running on http://localhost:3000.
All backend (`localhost:8000`) calls are intercepted and answered with
realistic mocked data so every protected screen renders correctly.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import Route, sync_playwright

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)

FRONT = "http://localhost:3000"
API = "http://localhost:8000"

# ---------- Mock data ----------------------------------------------------
SAMPLE_COURSES = [
    {
        "id": 1,
        "title": "مقدمة في الذكاء الاصطناعي",
        "description": "كورس تعريفي شامل بمفاهيم الذكاء الاصطناعي وتعلم الآلة وتطبيقاتها العملية.",
        "specialization": "Artificial Intelligence",
        "course_url": "https://www.youtube.com/watch?v=JMUxmLyrhSk",
        "course_type": "external",
        "is_active": "active",
        "thumbnail_url": "https://img.youtube.com/vi/JMUxmLyrhSk/maxresdefault.jpg",
        "instructor_id": 1,
        "instructor_name": "د. مها العتيبي",
        "created_at": "2026-04-12T10:00:00",
        "enrolled_count": 42,
    },
    {
        "id": 2,
        "title": "أساسيات بايثون للطلاب",
        "description": "تعلم لغة بايثون من الصفر مع تمارين تطبيقية ومشاريع مصغّرة.",
        "specialization": "Computer Science",
        "course_url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
        "course_type": "external",
        "is_active": "active",
        "thumbnail_url": "https://img.youtube.com/vi/_uQrJ0TkZlc/maxresdefault.jpg",
        "instructor_id": 1,
        "instructor_name": "د. مها العتيبي",
        "created_at": "2026-04-20T10:00:00",
        "enrolled_count": 87,
    },
    {
        "id": 3,
        "title": "الأمن السيبراني التطبيقي",
        "description": "مفاهيم الأمن السيبراني وحماية الأنظمة والشبكات والتطبيقات الحديثة.",
        "specialization": "Cybersecurity",
        "course_url": "https://www.coursera.org/learn/cyber-security-basics",
        "course_type": "external",
        "is_active": "active",
        "thumbnail_url": "",
        "instructor_id": 1,
        "instructor_name": "د. مها العتيبي",
        "created_at": "2026-05-01T10:00:00",
        "enrolled_count": 31,
    },
    {
        "id": 4,
        "title": "مقدمة في علم البيانات",
        "description": "أساسيات تحليل البيانات والتصور والتعلم الإحصائي باستخدام أدوات حديثة.",
        "specialization": "Data Science",
        "course_url": "https://www.youtube.com/watch?v=ua-CiDNNj30",
        "course_type": "external",
        "is_active": "active",
        "thumbnail_url": "https://img.youtube.com/vi/ua-CiDNNj30/maxresdefault.jpg",
        "instructor_id": 1,
        "instructor_name": "د. مها العتيبي",
        "created_at": "2026-05-08T10:00:00",
        "enrolled_count": 58,
    },
]

SAMPLE_ENROLLMENTS = [
    {
        "id": 10,
        "course_id": 2,
        "student_id": 5,
        "enrolled_at": "2026-05-02T09:30:00",
        "status": "active",
        "course": SAMPLE_COURSES[1],
    }
]

SAMPLE_FILES = [
    {
        "id": 1,
        "original_filename": "محاضرة 1 - مقدمة الذكاء الاصطناعي.pdf",
        "file_size": 1_245_312,
        "file_type": "application/pdf",
        "upload_time": "2026-05-08T11:20:00",
    },
    {
        "id": 2,
        "original_filename": "ملخص بايثون.pdf",
        "file_size": 532_900,
        "file_type": "application/pdf",
        "upload_time": "2026-05-09T08:45:00",
    },
]

SAMPLE_CHAT = {
    "messages": [
        {
            "id": 1,
            "message": "مرحبًا، ممكن تشرح لي مفهوم التعلم العميق باختصار؟",
            "response": (
                "بالتأكيد! التعلم العميق هو فرع من تعلم الآلة يستخدم شبكات عصبية متعددة الطبقات "
                "لاستخراج تمثيلات معقدة من البيانات. يُستخدم في الرؤية الحاسوبية، معالجة اللغات "
                "الطبيعية، التعرف على الكلام، والقيادة الذاتية. يعتمد على كميات كبيرة من البيانات "
                "وقدرات حسابية عالية (GPU/TPU) للتدريب."
            ),
            "created_at": "2026-05-10T09:00:00",
            "context": None,
        },
        {
            "id": 2,
            "message": "ما الفرق بين Supervised و Unsupervised Learning؟",
            "response": (
                "في التعلم المُوجَّه (Supervised) نستخدم بيانات مُصنّفة (Labels) لتدريب النموذج "
                "ليتنبأ بالمخرجات. أما التعلم غير المُوجَّه (Unsupervised) فيكتشف الأنماط في "
                "البيانات بدون تصنيفات مسبقة، مثل التجميع (Clustering) وتقليل الأبعاد."
            ),
            "created_at": "2026-05-10T09:02:00",
            "context": None,
        },
    ]
}

SAMPLE_STATS = {
    "total_documents": 12,
    "total_chunks": 348,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "vector_store": "PostgreSQL + pgvector",
    "status": "ready",
}

USERS = {
    "faculty": {
        "id": 1,
        "username": "dr_maha",
        "email": "maha@example.edu",
        "role": "faculty",
        "specialization": None,
        "is_active": True,
        "created_at": "2026-01-15T10:00:00",
    },
    "student": {
        "id": 5,
        "username": "sara_ali",
        "email": "sara@example.edu",
        "role": "student",
        "specialization": "Computer Science",
        "is_active": True,
        "created_at": "2026-02-20T10:00:00",
    },
    "admin": {
        "id": 99,
        "username": "admin",
        "email": "admin@example.edu",
        "role": "admin",
        "specialization": None,
        "is_active": True,
        "created_at": "2026-01-01T08:00:00",
    },
}


def make_router(user_key: str):
    """Return a route handler that mocks backend endpoints for a given user."""
    user = USERS.get(user_key)

    def handler(route: Route):
        req = route.request
        url = req.url
        method = req.method
        # CORS preflight
        if method == "OPTIONS":
            return route.fulfill(
                status=204,
                headers={
                    "access-control-allow-origin": "*",
                    "access-control-allow-headers": "*",
                    "access-control-allow-methods": "*",
                },
            )

        def J(data, status=200):
            return route.fulfill(
                status=status,
                content_type="application/json",
                headers={"access-control-allow-origin": "*"},
                body=json.dumps(data, ensure_ascii=False),
            )

        path = url.replace(API, "")
        # auth
        if path.startswith("/login"):
            return J({"access_token": "MOCK_TOKEN", "token_type": "bearer"})
        if path.startswith("/register"):
            return J(user or USERS["student"])
        if path.startswith("/me"):
            if user is None:
                return J({"detail": "Not authenticated"}, status=401)
            return J(user)
        # chat / rag
        if path == "/chat" and method == "GET":
            return J(SAMPLE_CHAT)
        if path == "/chat" and method == "POST":
            body = json.loads(req.post_data or "{}")
            return J(
                {
                    "id": 99,
                    "message": body.get("message", ""),
                    "response": (
                        "هذا مثال على ردّ ذكي من المساعد. تم استرجاع المعلومات من ملفات "
                        "المقرر المرفوعة وصياغة إجابة مختصرة ومدعومة بالمصادر."
                    ),
                    "created_at": "2026-05-15T10:00:00",
                    "context": [
                        {"source": "محاضرة 1 - مقدمة الذكاء الاصطناعي.pdf", "snippet": "..."}
                    ],
                }
            )
        if path == "/stats":
            return J(SAMPLE_STATS)
        if path == "/files":
            return J({"files": SAMPLE_FILES})
        if path == "/courses/my-courses":
            return J({"courses": SAMPLE_COURSES, "total": len(SAMPLE_COURSES)})
        if path == "/courses/my-enrollments":
            return J(SAMPLE_ENROLLMENTS)
        if path.startswith("/upload"):
            return J({"detail": "تم بنجاح (نموذج تجريبي)"})
        # Default
        return J({})

    return handler


def shoot(page, name: str):
    """Take a full-page screenshot with a small settle pause."""
    page.wait_for_load_state("networkidle", timeout=10_000)
    time.sleep(0.8)
    out = SHOTS / f"{name}.png"
    page.screenshot(path=str(out), full_page=True)
    print(f"saved {out.name}")
    return out


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA")
        page = ctx.new_page()

        # ---- Public pages (no auth) ---------------------------------------
        page.route(f"{API}/**", make_router(user_key="none"))

        page.goto(f"{FRONT}/login", wait_until="domcontentloaded")
        page.evaluate("localStorage.clear()")
        page.reload()
        shoot(page, "01_login")

        # Toggle role to student via dropdown
        try:
            page.select_option("select#role", "student")
            time.sleep(0.3)
            shoot(page, "01b_login_student_role")
        except Exception:
            pass

        page.goto(f"{FRONT}/register", wait_until="domcontentloaded")
        shoot(page, "02_register_faculty")

        try:
            page.select_option("select#role", "student")
            time.sleep(0.3)
            shoot(page, "02b_register_student")
        except Exception:
            pass

        # ---- Authenticated as FACULTY ------------------------------------
        page.unroute(f"{API}/**")
        page.route(f"{API}/**", make_router(user_key="faculty"))
        page.evaluate(
            "(u)=>{localStorage.setItem('token','MOCK_TOKEN');localStorage.setItem('mockUser', JSON.stringify(u));}",
            USERS["faculty"],
        )

        page.goto(f"{FRONT}/chat", wait_until="domcontentloaded")
        shoot(page, "03_chat_faculty")

        # Click "Upload Files" tab inside chat (if present)
        try:
            btn = page.get_by_role("button", name="Upload Files")
            if btn.count() > 0:
                btn.first.click()
                time.sleep(0.6)
                shoot(page, "03b_chat_faculty_upload_tab")
        except Exception:
            pass

        page.goto(f"{FRONT}/courses/faculty", wait_until="domcontentloaded")
        shoot(page, "04_faculty_courses")

        # Open the "Add new course" modal if a button exists
        try:
            for label in ["Add Course", "Add New Course", "+ Add", "إضافة كورس"]:
                btn = page.get_by_role("button", name=label)
                if btn.count() > 0:
                    btn.first.click()
                    time.sleep(0.6)
                    shoot(page, "04b_faculty_courses_modal")
                    page.keyboard.press("Escape")
                    break
        except Exception:
            pass

        # ---- Authenticated as STUDENT ------------------------------------
        page.unroute(f"{API}/**")
        page.route(f"{API}/**", make_router(user_key="student"))
        page.evaluate(
            "(u)=>{localStorage.setItem('token','MOCK_TOKEN');localStorage.setItem('mockUser', JSON.stringify(u));}",
            USERS["student"],
        )

        page.goto(f"{FRONT}/chat", wait_until="domcontentloaded")
        shoot(page, "05_chat_student")

        page.goto(f"{FRONT}/courses/student", wait_until="domcontentloaded")
        shoot(page, "06_student_courses_available")

        # Switch to "Enrolled" tab
        try:
            for label in ["Enrolled", "My Courses", "المسجلة"]:
                btn = page.get_by_role("button", name=label)
                if btn.count() > 0:
                    btn.first.click()
                    time.sleep(0.5)
                    shoot(page, "06b_student_courses_enrolled")
                    break
        except Exception:
            pass

        # ---- Authenticated as ADMIN (for the upload pages) ---------------
        page.unroute(f"{API}/**")
        page.route(f"{API}/**", make_router(user_key="admin"))
        page.evaluate(
            "(u)=>{localStorage.setItem('token','MOCK_TOKEN');localStorage.setItem('mockUser', JSON.stringify(u));}",
            USERS["admin"],
        )

        page.goto(f"{FRONT}/upload-students", wait_until="domcontentloaded")
        shoot(page, "07_upload_students")

        page.goto(f"{FRONT}/upload-faculty", wait_until="domcontentloaded")
        shoot(page, "08_upload_faculty")

        page.goto(f"{FRONT}/upload-staff", wait_until="domcontentloaded")
        shoot(page, "09_upload_staff")

        browser.close()
        print("done.")


if __name__ == "__main__":
    main()
