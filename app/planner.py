import re
from collections import defaultdict
from app.prerequisites import evaluate, PrerequisiteError

GROUPS={"university":("university_required","إجباري الجامعة"),"major_required":("speciality_required","إجباري التخصص"),
        "major_elective":("speciality_elective","اختياري التخصص"),"free_elective_option":("free_elective","اختياري حر")}

class Planner:
    def __init__(self,courses,report):
        self.courses={c["course_code"]:c for c in courses};self.report=report
        self.targets={r["requirement"]:int(r["credits"]) for r in report.get("requirements",[])}
    def plan(self,completed,proposed):
        done=set(completed);chosen=set(proposed)
        unknown=(done|chosen)-self.courses.keys()
        if unknown: raise ValueError("رموز غير موجودة في الخطة: "+", ".join(sorted(unknown)))
        if done&chosen: raise ValueError("لا يمكن اقتراح مساق مكتمل بالفعل.")
        raw=defaultdict(int)
        for code in done: raw[self.courses[code]["requirement_group"]]+=int(self.courses[code]["credit_hours"])
        categories=[]
        for group,(key,label) in GROUPS.items():
            target=self.targets.get(key)
            if target is None: raise ValueError("بيانات فئات متطلبات التخرج ناقصة.")
            categories.append({"key":group,"label":label,"earned":raw[group],"counted":min(raw[group],target),"required":target,"remaining":max(0,target-raw[group])})
        eligible=[];review=[];blocked=[]
        for code,c in self.courses.items():
            if code in done: continue
            flagged=any(t in c.get("prerequisite_review_status","") for t in ["ambiguous","conflicting"])
            credit_conflict=code=="11032102"
            if flagged or credit_conflict:
                review.append({**c,"review_reason":"تعارض أو غموض في المصدر؛ لا نؤكد الأهلية قبل التدقيق."});continue
            try: ok=evaluate(c["prerequisite_expression"],done)
            except PrerequisiteError:
                review.append({**c,"review_reason":"صيغة المتطلب تحتاج مراجعة."});continue
            if ok: eligible.append(c)
            else: blocked.append({**c,"missing_codes":sorted(set(re.findall(r"\d+",c["prerequisite_expression"]))-done)})
        eligible_codes={c["course_code"] for c in eligible}
        invalid=chosen-eligible_codes
        credits=sum(int(self.courses[c]["credit_hours"]) for c in chosen)
        warnings=["هذه محاكاة للخطة المورّدة، وليست موافقة تسجيل أو إثبات تخرج. لا نفحص عروض الفصل أو تعارض المواعيد أو الموافقات الخاصة.",
                  "الحد 18 ساعة قاعدة للنموذج؛ قد تختلف الاستثناءات الرسمية. استخدم سجلاً افتراضياً فقط."]
        if credits<12: warnings.append("العبء المختار أقل من 12 ساعة؛ راجع العمادة لتحديد ما ينطبق على الحالة.")
        if credits>18: warnings.append("العبء يتجاوز سقف النموذج البالغ 18 ساعة.")
        if invalid: warnings.append("تتضمن الخطة مساقات غير مستوفية للمتطلبات أو تحتاج مراجعة: "+", ".join(sorted(invalid)))
        if self.report.get("degree_conflicts"): warnings.append("تعارض موثق: الخطة المورّدة 162 ساعة، بينما الدليل المرفق يذكر 163. الأرقام التالية تقدير للخطة الموردة فقط.")
        flagged_done=[c for c in done if c=="11032102" or "ambiguous" in self.courses[c].get("prerequisite_review_status","")]
        if flagged_done: warnings.append("المساقات المكتملة المختارة تتضمن بيانات تحتاج مراجعة: "+", ".join(sorted(flagged_done)))
        completion_checks=[]
        for code in sorted(done):
            course=self.courses[code]
            try: valid=evaluate(course["prerequisite_expression"],done)
            except PrerequisiteError: valid=False
            if not valid:
                completion_checks.append({"course_code":code,"course_name_ar":course["course_name_ar"],"prerequisite_expression":course["prerequisite_expression"]})
        counted=sum(c["counted"] for c in categories)
        mandatory_remaining=[c["course_code"] for c in self.courses.values() if c["requirement_group"] in {"university","major_required"} and int(c["credit_hours"])>0 and c["course_code"] not in done]
        return {"completed_count":len(done),"earned_credits":sum(raw.values()),"counted_credits":counted,
                "remaining_credits":sum(c["remaining"] for c in categories),"plan_total":self.targets.get("total_credit_hours"),
                "categories":categories,"eligible":eligible,"needs_review":review,"blocked":blocked,"proposed_credits":credits,
                "proposal_valid":credits<=18 and not invalid,"warnings":warnings,
                "graduation_confirmed":False,"mandatory_remaining":mandatory_remaining,"completion_checks":completion_checks}
