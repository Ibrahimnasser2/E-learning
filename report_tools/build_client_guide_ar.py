# -*- coding: utf-8 -*-
"""Generate Arabic client user guide PDF for MANAMU (non-technical)."""
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "دليل_استخدام_منصة_مانامو.pdf"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_B = Path(r"C:\Windows\Fonts\arialbd.ttf")


def ar(text: str) -> str:
    """Shape + bidi for correct Arabic display in PDF."""
    return get_display(arabic_reshaper.reshape(text))


class GuidePDF(FPDF):
    def header(self):
        self.set_font("Arabic", "B", 11)
        self.set_text_color(26, 35, 126)
        self.cell(0, 8, ar("منصة مانامو التعليمية — دليل الاستخدام للعميل"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(92, 107, 192)
        self.set_line_width(0.4)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arabic", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, ar(f"صفحة {self.page_no()}"), align="C")

    def body(self, text):
        self.set_x(self.l_margin)
        self.set_font("Arabic", "", 12)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 8, ar(text), align="R")
        self.ln(1)

    def step(self, num, text):
        self.set_x(self.l_margin)
        self.set_font("Arabic", "B", 12)
        self.set_text_color(26, 35, 126)
        self.multi_cell(0, 8, ar(f"الخطوة {num}:"), align="R")
        self.set_x(self.l_margin)
        self.set_font("Arabic", "", 12)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 8, ar(text), align="R")
        self.ln(2)

    def tip(self, text):
        self.set_x(self.l_margin)
        self.set_fill_color(232, 234, 246)
        self.set_font("Arabic", "", 11)
        self.set_text_color(40, 53, 147)
        self.multi_cell(0, 7, ar("ملاحظة: " + text), align="R", fill=True)
        self.ln(3)

    def bullet(self, text):
        self.set_x(self.l_margin)
        self.set_font("Arabic", "", 12)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 7, ar("- " + text), align="R")

    def h1(self, text):
        self.set_x(self.l_margin)
        self.set_font("Arabic", "B", 16)
        self.set_text_color(26, 35, 126)
        self.multi_cell(0, 10, ar(text), align="R")
        self.ln(2)

    def h2(self, text):
        self.set_x(self.l_margin)
        self.set_font("Arabic", "B", 13)
        self.set_text_color(40, 53, 147)
        self.multi_cell(0, 9, ar(text), align="R")
        self.ln(1)


def build():
    if not FONT.exists():
        raise SystemExit(f"Arabic font not found: {FONT}")

    pdf = GuidePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Arabic", "", str(FONT))
    pdf.add_font("Arabic", "B", str(FONT_B if FONT_B.exists() else FONT))
    pdf.add_page()

    pdf.h1("دليل استخدام منصة مانامو (MANAMU)")
    pdf.body(
        "هذا الدليل يشرح لك كيفية استخدام المنصة خطوة بخطوة، بلغة بسيطة. "
        "لا تحتاج أي خلفية تقنية — فقط اتبع الترتيب كما هو مكتوب."
    )
    pdf.ln(2)

    pdf.h2("من يستخدم المنصة؟")
    pdf.bullet("المسؤول (الإداري): ينشئ حسابات الطلاب والدكاترة من ملفات إكسل.")
    pdf.bullet("الدكتور: يربط الطلاب بمستوياتهم، ينشئ المقررات، ويرفع ملفات الشرح (PDF).")
    pdf.bullet("الطالب: يفتح مقررات مستواه ويسأل المساعد الذكي عن محتوى الملفات.")
    pdf.ln(2)

    pdf.h2("ترتيب العمل الصحيح (مهم)")
    pdf.body("اعمل دائمًا بهذا الترتيب:")
    pdf.bullet("أولًا: دخول المسؤول ورفع ملفات الحسابات.")
    pdf.bullet("ثانيًا: دخول الدكتور ورفع قائمة الطلاب بالمستوى.")
    pdf.bullet("ثالثًا: الدكتور ينشئ المقرر في منصة التعلم ويختار المستوى.")
    pdf.bullet("رابعًا: الدكتور يرفع ملفات المواد (PDF).")
    pdf.bullet("خامسًا: دخول الطالب والسؤال في المحادثة.")
    pdf.tip("لو عملت خطوة قبل اللي قبلها، ممكن ما تظهرش الحسابات أو المقررات — رجّع للترتيب.")

    # —— Admin ——
    pdf.add_page()
    pdf.h1("القسم الأول: عمل المسؤول (الإداري)")

    pdf.h2("١) تسجيل الدخول بحساب المسؤول")
    pdf.step(1, "افتح رابط المنصة من المتصفح.")
    pdf.step(2, "في صفحة الدخول اكتب اسم المستخدم أو البريد الخاص بالمسؤول، ثم كلمة المرور.")
    pdf.step(3, "اضغط زر الدخول. ستفتح لك شاشة الإدارة.")
    pdf.tip(
        "حساب المسؤول الافتراضي في النظام: اسم المستخدم maha — "
        "أو البريد eng-maha@gmail.com — وكلمة المرور maha1234 "
        "(يمكن تغييرها لاحقًا حسب سياسة الجهة)."
    )

    pdf.h2("٢) تجهيز ملف طلاب (إكسل)")
    pdf.body("حضّر ملف إكسل للطلاب فيه ثلاثة أعمدة فقط:")
    pdf.bullet("الرقم الجامعي")
    pdf.bullet("الاسم")
    pdf.bullet("الهاتف")
    pdf.body("مثال:")
    pdf.bullet("441234567 | سارة محمد | 0501234567")
    pdf.tip(
        "بعد الرفع، النظام ينشئ للطالب تلقائيًا: اسم الدخول = الرقم الجامعي، "
        "وكلمة المرور = MANAMU + آخر 4 أرقام من الرقم الجامعي. "
        "مثال: الرقم ينتهي بـ 4567 ← كلمة المرور MANAMU4567"
    )

    pdf.h2("٣) تجهيز ملف دكاترة (إكسل)")
    pdf.body("حضّر ملف إكسل للدكاترة فيه ثلاثة أعمدة:")
    pdf.bullet("الاسم")
    pdf.bullet("البريد الجامعي (ينتهي بـ @kk.edu.sa)")
    pdf.bullet("الهاتف")
    pdf.body("مثال:")
    pdf.bullet("د. أحمد علي | ahmed.ali@kk.edu.sa | 0501112233")
    pdf.tip(
        "اسم الدخول للدكتور = الجزء قبل علامة @ في البريد (مثل: ahmed.ali). "
        "كلمة المرور = MANAMU + آخر 4 حروف/أرقام من نفس الجزء. "
        "مثال ahmed.ali ← كلمة المرور MANAMU.ali"
    )

    pdf.h2("٤) رفع الملفات من شاشة الإدارة")
    pdf.step(1, "من شاشة الإدارة اختر ملف الطلاب (Excel) ثم ارفعه.")
    pdf.step(2, "انتظر رسالة النجاح وتأكد من عدد الحسابات المضافة.")
    pdf.step(3, "كرر نفس الشيء لملف الدكاترة.")
    pdf.step(4, "بعد الانتهاء اضغط تسجيل الخروج.")
    pdf.tip(
        "يمكن تحميل قالب جاهز من نفس شاشة الإدارة (زر تنزيل القالب) ثم تعبئته ورفعه."
    )

    # —— Faculty ——
    pdf.add_page()
    pdf.h1("القسم الثاني: عمل الدكتور")

    pdf.h2("١) تسجيل دخول الدكتور")
    pdf.step(1, "افتح المنصة من المتصفح.")
    pdf.step(2, "ادخل باسم المستخدم (مثل ahmed.ali) وكلمة المرور التي أنشأها النظام.")
    pdf.step(3, "ستفتح واجهة المحادثة مع قائمة جانبية.")

    pdf.h2("٢) رفع طلاب المقرر (ربط الطلاب بالمستوى)")
    pdf.body(
        "هذه الخطوة مهمة جدًا: بدونها الطالب لن يظهر له المقرر الصحيح. "
        "من القائمة الجانبية اختر Upload Students."
    )
    pdf.step(1, "حضّر ملف إكسل بالأعمدة: الرقم الجامعي — المستوى — المقررات (اختياري).")
    pdf.step(2, "المستوى رقم من 1 إلى 5 (مثلًا 1 = المستوى الأول).")
    pdf.step(3, "الرقم الجامعي لازم يكون لنفس الطلاب اللي رفعهم المسؤول قبل كده.")
    pdf.step(4, "ارفع الملف وانتظر رسالة النجاح.")
    pdf.body("مثال صف واحد:")
    pdf.bullet("441234567 | 1 | 1001 انجل, 1202 تقن")
    pdf.tip(
        "لو حابب تقدر تنزّل قالب من نفس الشاشة. "
        "العمود «المقررات» يساعد في توجيه المواد؛ والأهم للطالب هو رقم المستوى."
    )

    pdf.h2("٣) إنشاء مقرر في منصة التعلم (Learning Platform)")
    pdf.step(1, "من القائمة الجانبية افتح Learning Platform.")
    pdf.step(2, "اضغط Create Course (إنشاء مقرر).")
    pdf.step(3, "اكتب عنوان المقرر (أو اختر المادة فتُملأ تلقائيًا).")
    pdf.step(4, "اختر المستوى أولًا (مثل: الأول).")
    pdf.step(5, "بعد اختيار المستوى ستظهر المواد الخاصة به في قائمة التخصص/المادة — اختر المادة المطلوبة.")
    pdf.step(6, "احفظ المقرر.")
    pdf.tip(
        "المقرر يظهر فقط لطلاب نفس المستوى. "
        "طلاب المستوى 2 لن يروا مقرر المستوى 1."
    )

    pdf.h2("٤) رفع ملفات الشرح (PDF)")
    pdf.step(1, "من الشريط العلوي أو القائمة اختر Upload Materials.")
    pdf.step(2, "حدّد لمن الملف: طلاب / أعضاء هيئة تدريس / الاثنين.")
    pdf.step(3, "إذا اخترت الطلاب: اختر المستوى ثم اختر مقررًا أو أكثر من قائمة المستوى.")
    pdf.step(4, "اختر ملف PDF من جهازك ثم ارفعه.")
    pdf.step(5, "انتظر حتى تظهر حالة الملف Ready (جاهز).")
    pdf.tip(
        "الطالب يرى الملف فقط إذا كان مسجّلًا في نفس المقرر/المستوى، "
        "وبعد تاريخ تسجيله — الملفات القديمة قبل تسجيله لا تظهر له."
    )

    pdf.h2("٥) سؤال المساعد الذكي (كالدكتور)")
    pdf.step(1, "ارجع لتبويب Chat.")
    pdf.step(2, "اكتب سؤالك عن محتوى الملفات التي رفعتها أنت.")
    pdf.step(3, "المساعد يجيب من ملفاتك فقط (ما لم تفعّل البحث على الويب).")

    # —— Student ——
    pdf.add_page()
    pdf.h1("القسم الثالث: عمل الطالب")

    pdf.h2("١) تسجيل دخول الطالب")
    pdf.step(1, "افتح المنصة.")
    pdf.step(2, "اسم الدخول = الرقم الجامعي.")
    pdf.step(3, "كلمة المرور = MANAMU + آخر 4 أرقام من الرقم الجامعي.")
    pdf.body("مثال: الرقم 441234567 ← الدخول 441234567 وكلمة المرور MANAMU4567")

    pdf.h2("٢) رؤية المقررات")
    pdf.step(1, "من القائمة الجانبية افتح My Courses أو Learning Platform الخاصة بالطالب.")
    pdf.step(2, "ستظهر المقررات التي أنشأها الدكتور لمستواك فقط.")
    pdf.tip("إذا القائمة فارغة: تأكد أن الدكتور رفعك بالمستوى الصحيح وأنشأ مقررًا لهذا المستوى.")

    pdf.h2("٣) الملفات والمحادثة")
    pdf.step(1, "من تبويب My Files يمكنك رؤية ملفات مستواك مجمّعة حسب المقرر.")
    pdf.step(2, "من تبويب Chat اختر المقرر إن طُلب منك، ثم اكتب سؤالك.")
    pdf.step(3, "المساعد يجيب من ملفات مقررك — لا من مقررات المستويات الأخرى.")

    # —— Checklist ——
    pdf.add_page()
    pdf.h1("قائمة تحقق سريعة قبل التسليم للعميل")
    pdf.bullet("المسؤول رفع ملف الطلاب وملف الدكاترة بنجاح.")
    pdf.bullet("تجربة دخول دكتور واحد على الأقل تعمل.")
    pdf.bullet("الدكتور رفع ملف ربط الطلاب بالمستوى.")
    pdf.bullet("الدكتور أنشأ مقررًا في Learning Platform مع اختيار المستوى.")
    pdf.bullet("الدكتور رفع PDF وانتظر حتى صار Ready.")
    pdf.bullet("طالب من نفس المستوى يرى المقرر ويسأل ويجيبه المساعد.")
    pdf.bullet("طالب من مستوى آخر لا يرى مقرر المستوى المختلف.")
    pdf.ln(4)

    pdf.h2("أسئلة شائعة بسيطة")
    pdf.body("س: ليه حساب الدكتور/الطالب مش شغال؟")
    pdf.body("ج: غالبًا الملف ما اترف عش عند المسؤول، أو كلمة المرور مكتوبة غلط. راجع أمثلة كلمة المرور أعلاه.")
    pdf.ln(1)
    pdf.body("س: ليه الطالب ما يشوفش المقرر؟")
    pdf.body(
        "ج: لازم الدكتور يرفع ملف المستوى للطالب، ثم ينشئ المقرر لنفس المستوى في Learning Platform."
    )
    pdf.ln(1)
    pdf.body("س: ليه المساعد يقول مفيش معلومات؟")
    pdf.body("ج: ارفع PDF أولًا وانتظر Ready، وتأكد أن السؤال عن محتوى الملف المرفوع لنفس المقرر.")
    pdf.ln(4)

    pdf.h2("خلاصة")
    pdf.body(
        "المسؤول ينشئ الحسابات ← الدكتور يربط المستوى وينشئ المقرر ويرفع الملفات ← "
        "الطالب يدخل ويسأل. هذا كل شيء — بنفس الترتيب."
    )
    pdf.ln(6)
    pdf.set_font("Arabic", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 6, ar("منصة مانامو التعليمية — دليل استخدام للعميل"), align="C")

    pdf.output(str(OUT))
    print(f"Wrote: {OUT}")


if __name__ == "__main__":
    build()
