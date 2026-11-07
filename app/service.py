import secrets
import threading
import time
from collections import OrderedDict
from app.generation import Generator
from app.schemas import ChatResponse

class Sessions:
    """Bounded ephemeral demo memory; no transcripts or identities are persisted."""
    def __init__(self): self.items=OrderedDict();self.lock=threading.Lock()
    def get(self,session_id):
        with self.lock:
            now=time.monotonic()
            for key in list(self.items):
                if now-self.items[key][0]>3600: self.items.pop(key,None)
            if session_id not in self.items: session_id=secrets.token_urlsafe(24)
            self.items.setdefault(session_id,(now,[]))
            self.items.move_to_end(session_id)
            while len(self.items)>128: self.items.popitem(last=False)
            return session_id,list(self.items[session_id][1])
    def add(self,session_id,question):
        with self.lock:
            if session_id in self.items:
                history=self.items[session_id][1]
                self.items[session_id]=(time.monotonic(),(history+[question])[-4:])

class Advisor:
    def __init__(self,retriever,cfg): self.retriever=retriever;self.generator=Generator(cfg);self.sessions=Sessions()
    def chat(self,request,profile=None):
        sid,history=self.sessions.get(request.conversation_id)
        q=request.question.strip()
        if not q: raise ValueError("اكتب سؤالك أولاً.")
        # Previous questions disambiguate retrieval only. The generator sees them separately.
        contextual="\n".join(history[-2:]+[q]) if history else q
        from app.progress import is_remaining_question
        if profile and is_remaining_question(q):
            conflicts=self.retriever.report.get("degree_conflicts",[])
            evidence=[c for c in getattr(self.retriever,"chunks",[]) if c.get("kind")=="degree_requirements" or any(c.get("document_id")==v["document_id"] and c.get("page_start")==v["page"] for v in conflicts)]
        else:
            evidence=self.retriever.retrieve(contextual)
        report={**self.retriever.report,"response_language":request.language}
        if profile:
            from app.planner import Planner
            plan=Planner(self.retriever.courses,self.retriever.report).plan(profile["completed"],[])
            context={"study_year":profile["study_year"],"completed_codes":profile["completed"],
                     "completed_courses":[{"code":c["course_code"],"name":c["course_name_ar"]} for c in self.retriever.courses if c["course_code"] in profile["completed"]],
                     "counted_credits":plan["counted_credits"],"remaining_plan_credits":plan["remaining_credits"],
                     "plan_total":plan["plan_total"],"categories":plan["categories"],
                     "eligible_by_listed_prerequisites":[{"code":c["course_code"],"name":c["course_name_ar"]} for c in plan["eligible"]],
                     "completion_checks":plan["completion_checks"],"warnings":plan["warnings"],"graduation_confirmed":False}
            report["student_context"]=context
            import json
            evidence=evidence+[{"source_id":"profile:current","document_id":"student_profile","document_name":"ملفك الدراسي والحسابات المبنية على الخطة",
              "text":json.dumps(context,ensure_ascii=False),"source_url":"","record_id":"saved_profile","version":"السجل المحفوظ الحالي",
              "verification_status":"user_selected_completion_and_deterministic_calculation"}]
        from app.progress import progress_answer
        result=progress_answer(q,request.language,report,evidence) if profile else None
        if result is None:
            result=self.generator.generate(q,evidence,history,request.style,report)
        self.sessions.add(sid,q)
        return ChatResponse(**result,conversation_id=sid)
