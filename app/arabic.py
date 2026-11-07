import re
import unicodedata

DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
LETTERS = str.maketrans({"أ":"ا", "إ":"ا", "آ":"ا", "ٱ":"ا", "ى":"ي"})
STOP = set("ما ماذا هل هو هي في من على عن الى الي ان اذا او و كم شو قديش بدي انا هاي هاد هذا هذه طيب ممكن بقدر فيني فيي فينا مش عم بديش".split())
STOP.update("حسب دليل الطالب طالب جامعة الجامعة النجاح الوطنية 2026 2027".split())
ALIASES = {
    "اسحب": "انسحاب سحب", "اسحبه": "انسحاب سحب", "انسحب": "انسحاب سحب", "سحبت": "انسحاب سحب",
    "احذف": "حذف اضافة", "احذفها": "حذف اضافة", "انزل": "تسجيل عبء دراسي ساعات", "اسجل": "تسجيل عبء دراسي ساعات",
    "سجل": "تسجيل", "غبت": "غياب مواظبة حضور", "غيابي": "غياب مواظبة حضور", "بحضر": "حضور مواظبة",
    "رسبت": "رسوب اعادة متطلب سابق", "اعد": "اعادة", "اعيد": "اعادة", "ارجع": "اعادة",
    "انذار": "انذار معدل تراكمي", "معدلي": "معدل تراكمي", "اتخرج": "تخرج متطلبات", "ضايل": "متبقي تخرج",
    "بعدها": "متطلب سابق", "بالصيفي": "الفصل الصيفي", "هالفصل": "الفصل الدراسي", "باخد": "تسجيل",
}

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(DIGITS).translate(LETTERS).lower()
    text = re.sub(r"[\u064b-\u065f\u0670\u06d6-\u06edـ]", "", text)
    text = re.sub(r"\bاال(?=[\u0621-\u064a])", "ال", text)
    return re.sub(r"\s+", " ", text).strip()

def tokens(text: str) -> list[str]:
    result=[]
    for t in re.findall(r"[\w]+", normalize(text)):
        if t in STOP or len(t)<2: continue
        result.append(t)
        if t.startswith("ال") and len(t)>4: result.append(t[2:])
    return result

def search_variants(question: str) -> list[str]:
    n = normalize(question)
    extras = [ALIASES[t] for t in re.findall(r"[\w]+", n) if t in ALIASES]
    return [question] + ([n + " " + " ".join(extras)] if extras else [])
