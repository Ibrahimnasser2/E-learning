"""
Official program curriculum by academic level (الأول … الخامس).
Used when faculty selects Level → Courses for material upload / student linking.
"""

CURRICULUM_LEVELS = [
    {"id": "1", "label_ar": "الأول", "label_en": "Level 1"},
    {"id": "2", "label_ar": "الثاني", "label_en": "Level 2"},
    {"id": "3", "label_ar": "الثالث", "label_en": "Level 3"},
    {"id": "4", "label_ar": "الرابع", "label_en": "Level 4"},
    {"id": "5", "label_ar": "الخامس", "label_en": "Level 5"},
]

# code is unique within the program (number + department suffix)
CURRICULUM_COURSES = [
    # —— الأول ——
    {"code": "1001 انجل", "title": "مهارات اللغة الإنجليزية (1)", "level": "1", "credit_hours": 6, "specialization": "General"},
    {"code": "1103 احص", "title": "مقدمة في الإحصاء", "level": "1", "credit_hours": 3, "specialization": "General"},
    {"code": "1202 تقن", "title": "مهارات الحاسب", "level": "1", "credit_hours": 3, "specialization": "General"},
    {"code": "1202 فجب", "title": "اللياقة والثقافة الصحية", "level": "1", "credit_hours": 1, "specialization": "General"},
    {"code": "1203 نهج", "title": "مهارات التعلم والتفكير والبحث", "level": "1", "credit_hours": 3, "specialization": "General"},
    # —— الثاني ——
    {"code": "1210 وجت", "title": "أساسيات البرمجة", "level": "2", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "1211 وجت", "title": "أساسيات التصميم", "level": "2", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "1212 وجت", "title": "أساسيات الوسائط التفاعلية", "level": "2", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "1213 حاسب", "title": "مهارات الحاسب (2)", "level": "2", "credit_hours": 3, "specialization": "General"},
    {"code": "1213 وجت", "title": "مفاهيم في الإبداع", "level": "2", "credit_hours": 2, "specialization": "Web Development"},
    {"code": "2410 سلم", "title": "أخلاقيات المهنة", "level": "2", "credit_hours": 2, "specialization": "General"},
    # —— الثالث ——
    {"code": "2310 ويب", "title": "تصميم وتطوير مواقع الانترنت", "level": "3", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2311 جرف", "title": "معالجة الصور الرقمية", "level": "3", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2311 ويب", "title": "تصميم واجهة المستخدم", "level": "3", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2312 ويب", "title": "أساسيات الشبكات", "level": "3", "credit_hours": 3, "specialization": "Web Development"},
    # —— الرابع ——
    {"code": "2410 ويب", "title": "تصميم وتطوير مواقع الانترنت (2)", "level": "4", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2411 ويب", "title": "استضافة المواقع وبروتوكولات الإنترنت", "level": "4", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2412 ويب", "title": "تصميم المواقع المتجاوبة", "level": "4", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "2413 ويب", "title": "إدارة محتوى الويب", "level": "4", "credit_hours": 3, "specialization": "Web Development"},
    # —— الخامس ——
    {"code": "3510 ويب", "title": "مشروع تخرج", "level": "5", "credit_hours": 3, "specialization": "Web Development"},
    {"code": "3511 ويب", "title": "تدريب ميداني", "level": "5", "credit_hours": 9, "specialization": "Web Development"},
]


def get_levels():
    return list(CURRICULUM_LEVELS)


def get_courses_for_level(level_id: str):
    lid = str(level_id).strip()
    return [c for c in CURRICULUM_COURSES if str(c["level"]) == lid]


def find_catalog_course(code: str):
    if not code:
        return None
    needle = " ".join(str(code).split())
    for c in CURRICULUM_COURSES:
        if c["code"] == needle:
            return c
    # allow match without Arabic spaces quirks
    needle_compact = needle.replace(" ", "")
    for c in CURRICULUM_COURSES:
        if c["code"].replace(" ", "") == needle_compact:
            return c
    return None


def level_label(level_id: str) -> str:
    for lv in CURRICULUM_LEVELS:
        if lv["id"] == str(level_id):
            return f"{lv['label_ar']} ({lv['label_en']})"
    return str(level_id)
