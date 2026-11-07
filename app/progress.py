"""Answer personal credit totals from verified backend calculations, never model arithmetic."""
import re
from app.arabic import normalize
from app.generation import citation

def is_remaining_question(question):
    q=normalize(question)
    return bool(re.search(r"ساع(?:ة|ات)|credit|hours",q) and re.search(r"ضايل|ضايلي|متبق|باقي|بقي|remain|left",q) and re.search(r"كم|قديش|اديش|how many|what.*remain|remaining credits",q))

def progress_answer(question,language,report,evidence):
    context=report.get("student_context")
    if not context or not is_remaining_question(question):return None
    source=next((c for c in evidence if c["source_id"]=="profile:current"),None)
    if not source:return None
    sources=[citation(source)]
    plan_source=next((c for c in evidence if c.get("kind")=="degree_requirements" and c.get("record_key")=="total_credit_hours"),None)
    if plan_source:sources.append(citation(plan_source))
    labels={"university":"University requirements","major_required":"Major requirements","major_elective":"Major electives","free_elective_option":"Free electives"}
    remaining=context["remaining_plan_credits"];counted=context["counted_credits"];total=context["plan_total"]
    if language=="en":
        answer=f"Based on your saved completed courses, {counted} credits count toward the supplied {total}-credit plan, leaving {remaining} credits across its requirement categories. [1]"
        if plan_source:answer+=" [2]"
        answer+="\n\nRemaining by category:\n"+"\n".join(f"• {labels.get(c['key'],c['key'])}: {c['remaining']} credits" for c in context['categories'])+" [1]"
        caution="This is a calculation against the supplied plan, not confirmation of graduation."
    else:
        answer=f"حسب المساقات المنجزة التي حفظتها، يُحتسب لك {counted} ساعة ضمن الخطة المورّدة البالغة {total} ساعة، والمتبقي {remaining} ساعة موزّعة على فئات المتطلبات. [1]"
        if plan_source:answer+=" [2]"
        answer+="\n\nالمتبقي بحسب الفئة:\n"+"\n".join(f"• {c['label']}: {c['remaining']} ساعة" for c in context['categories'])+" [1]"
        caution="هذا حساب وفق الخطة المورّدة، وليس تأكيداً لاستيفاء شروط التخرج."
    conflicts=report.get("degree_conflicts",[])
    if conflicts:
        c=conflicts[0]
        guide=next((e for e in evidence if e.get("document_id")==c["document_id"] and e.get("page_start")==c["page"]),None)
        marker=""
        if guide:sources.append(citation(guide));marker=f" [{len(sources)}]"
        answer+=(f"\n\nتنبيه: الدليل المرفق يذكر {c['value']} ساعة، وهو مختلف عن الخطة المورّدة. أكّد الخطة المنطبقة مع القسم." if language=="ar" else f"\n\nNote: the attached guide lists {c['value']} credits, which differs from the supplied plan. Confirm your applicable plan with the department.")+marker
    answer+="\n\n"+caution
    if context.get("completion_checks"):
        answer+=("\nراجع قائمتك أيضاً: توجد مساقات منجزة لم تحدد متطلباتها السابقة." if language=="ar" else "\nReview your selections: some completed courses have unselected prerequisites.")+" [1]"
    return {"answer":answer,"status":"partially_answered" if conflicts else "answered","sources":sources,
            "limitations":[caution],"usage":{"model":None,"calls":0,"calculation":"deterministic_category_caps"}}
