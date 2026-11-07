from types import SimpleNamespace
from app.service import Advisor,Sessions
from app.schemas import ChatRequest
class Retriever:
    courses=[{'course_code':'10000001','course_name_ar':'مساق أول','credit_hours':'3','requirement_group':'major_required','prerequisite_expression':'','prerequisite_review_status':'clear'},
             {'course_code':'10000002','course_name_ar':'مساق ثان','credit_hours':'3','requirement_group':'major_required','prerequisite_expression':'10000001','prerequisite_review_status':'clear'}]
    report={'requirements':[{'requirement':k,'credits':v} for k,v in [('total_credit_hours',162),('university_required',19),('speciality_required',126),('speciality_elective',15),('free_elective',2)]]}
    def retrieve(self,q):return []
def test_saved_completed_courses_and_prerequisites_reach_generator():
    advisor=Advisor.__new__(Advisor);advisor.retriever=Retriever();advisor.sessions=Sessions()
    captured={}
    def generate(q,e,h,s,r):
        captured.update(report=r,evidence=e)
        return {'answer':'Answer','status':'answered','sources':[]}
    advisor.generator=SimpleNamespace(generate=generate)
    advisor.chat(ChatRequest(question='What can I take?',language='en'),{'study_year':2,'completed':['10000001']})
    context=captured['report']['student_context']
    assert context['completed_codes']==['10000001']
    assert context['eligible_by_listed_prerequisites']==[{'code':'10000002','name':'مساق ثان'}]
    assert captured['report']['response_language']=='en'
    assert captured['evidence'][-1]['source_id']=='profile:current'


def test_remaining_credits_use_saved_profile_without_llm_or_semantic_search():
    advisor=Advisor.__new__(Advisor);advisor.retriever=Retriever();advisor.sessions=Sessions()
    def forbidden(*args):raise AssertionError('Credit totals must not depend on Gemini or semantic search')
    advisor.generator=SimpleNamespace(generate=forbidden)
    advisor.retriever.retrieve=forbidden
    for language,q in [('ar','كم ساعة ضايل حسب المساقات اللي خلصتها؟'),('en','How many credits remain based on my completed courses?')]:
        response=advisor.chat(ChatRequest(question=q,language=language),{'study_year':2,'completed':['10000001']})
        assert response.status=='answered'
        assert '159' in response.answer and '162' in response.answer
        assert response.sources[0].source_id=='profile:current'
        assert response.usage['calls']==0
