import json
from types import SimpleNamespace
import pytest
from app.config import Settings
from app.generation import Generator,ProviderError,ConfigurationError

EVIDENCE=[{"source_id":"real:row:2","document_id":"catalog","document_name":"جدول المساقات","source_url":"https://www.najah.edu/","text":"رمز المساق 12345678؛ الساعات 3","version":"supplied","verification_status":"supplied_csv"}]

def mock_client(monkeypatch,answers):
    calls=[]
    class Models:
        def generate_content(self,**kwargs):
            calls.append(kwargs)
            item=answers[len(calls)-1]
            if isinstance(item,Exception):raise item
            return SimpleNamespace(text=json.dumps(item,ensure_ascii=False),usage_metadata=SimpleNamespace(prompt_token_count=10,candidates_token_count=5))
    client=SimpleNamespace(models=Models(),close=lambda:None)
    monkeypatch.setattr('app.generation.genai.Client',lambda **kwargs:client)
    return calls

def test_grounded_claims_are_checked_and_numbered(monkeypatch):
    calls=mock_client(monkeypatch,[{"status":"answered","claims":[{"text":"المساق ثلاث ساعات.","source_ids":["real:row:2"]}]},{"supported":True,"unsupported_claim_indexes":[]}])
    result=Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('كم ساعة؟',EVIDENCE,[],'levantine',{})
    assert len(calls)==2 and result['usage']['calls']==2
    assert result['answer']=='المساق ثلاث ساعات. [1]'
    assert result['sources'][0].record_id is None
    assert result['sources'][0].page_start is None
    assert 'شامية فلسطينية' in calls[0]['contents']

def test_failed_support_check_is_not_reported_as_absent_evidence(monkeypatch):
    mock_client(monkeypatch,[{"status":"answered","claims":[{"text":"يسمح بثلاثين ساعة.","source_ids":["real:row:2"]}]},{"supported":False,"unsupported_claim_indexes":[0]}])
    with pytest.raises(ProviderError):Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('سؤال',EVIDENCE,[],'formal',{})

def test_forged_source_fails_before_support_request(monkeypatch):
    calls=mock_client(monkeypatch,[{"status":"answered","claims":[{"text":"ادعاء","source_ids":["fake"]}]}])
    with pytest.raises(ProviderError):Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('سؤال',EVIDENCE,[],'formal',{})
    assert len(calls)==1

def test_clarification_is_distinct(monkeypatch):
    mock_client(monkeypatch,[{"status":"needs_clarification","claims":[],"clarification_question":"ما رمز المساق المقصود؟"}])
    result=Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('بقدر اسجلها؟',EVIDENCE,[],'formal',{})
    assert result['status']=='needs_clarification' and not result['sources']

def test_refusal_does_not_render_unsourced_model_message(monkeypatch):
    mock_client(monkeypatch,[{"status":"insufficient_evidence","claims":[],"message":"يسمح بتسجيل 30 ساعة"}])
    result=Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('سؤال',EVIDENCE,[],'formal',{})
    assert '30' not in result['answer'] and result['status']=='insufficient_evidence'

def test_provider_error_sanitized(monkeypatch):
    mock_client(monkeypatch,[RuntimeError('secret-test-credential')])
    with pytest.raises(ProviderError) as error:Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('سؤال',EVIDENCE,[],'formal',{})
    assert 'secret-test' not in str(error.value)

def test_missing_key_never_calls_provider():
    with pytest.raises(ConfigurationError):Generator(Settings(gemini_api_key='')).generate('سؤال',EVIDENCE,[],'formal',{})


def test_short_source_alias_maps_to_original_citation(monkeypatch):
    calls=mock_client(monkeypatch,[{"status":"answered","claims":[{"text":"المساق ثلاث ساعات.","source_ids":["S1"]}]},{"supported":True,"unsupported_claim_indexes":[]}])
    result=Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('كم ساعة؟',EVIDENCE,[],'formal',{})
    assert result['sources'][0].source_id=='real:row:2'
    assert json.loads(calls[0]['contents'])['context'][0]['source_id']=='S1'
    assert json.loads(calls[1]['contents'])['claims'][0]['source_ids']==['S1']
    schema=calls[0]['config'].response_schema.model_json_schema()
    assert 'S1' in str(schema)

def test_empty_evidence_refusal_respects_english():
    result=Generator(Settings(gemini_api_key='test-not-a-real-key')).generate('Question',[],[],'formal',{'response_language':'en'})
    assert result['answer'].startswith('The available documents')
