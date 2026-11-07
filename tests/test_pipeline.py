import json
import re
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.ingestion import collect, split_text
from app.config import Settings
from app.schemas import Draft, Claim
from app.generation import validate_draft, ProviderError, citation
from app.service import Sessions
from app.retrieval import rrf
from app.storage import build_db, load_table

class Tokenizer:
    def __call__(self,text,**kwargs):return {"offset_mapping":[m.span() for m in re.finditer(r"\S+",text)]}
class DiagnosticEmbedder:
    tokenizer=Tokenizer()
    def count(self,text):return len(text.split())

@pytest.fixture(scope="module")
def corpus():return collect(Settings(),DiagnosticEmbedder())

def test_real_ingestion_provenance(corpus):
    chunks,courses,docs,report,pages=corpus
    assert len(courses)==125
    assert any(d.get("page_count")==135 for d in docs)
    assert any(c["page_start"]==79 and "المواظب" in c["text"] for c in chunks)
    assert not any(c["document_name"] in {"README.md","collection_gaps.csv"} for c in chunks)
    assert not any("user_selected_prototype" in c["text"] for c in chunks)
    assert any(c["value"]==163 and c["page"]==47 for c in report["degree_conflicts"])
    assert all(c["record_id"] for c in chunks if c["kind"]!="pdf")
    assert len({c["source_id"] for c in chunks})==len(chunks)

def test_reading_order(corpus):
    pages=corpus[4]
    assert "دليل الطالب" in " ".join(pages[0]["text"].split())
    assert "هندسة الحاسوب" in next(p["text"] for p in pages if p["page"]==47)

def test_chunking_preserves_text():
    text="الجملة الأولى.\n"+" ".join(f"كلمة{i}" for i in range(100))
    pieces=list(split_text(text,Tokenizer(),20,3))
    assert len(pieces)>4
    assert all(piece in text for piece in pieces)
    assert "كلمة99" in pieces[-1]

def test_persistence(corpus,tmp_path):
    chunks,courses,docs,report,_=corpus
    path=tmp_path/"knowledge.sqlite"
    build_db(path,chunks,courses,docs,{"report":report})
    assert len(load_table(path,"courses"))==125
    build_db(path,chunks,courses,docs,{"report":report})
    assert len(load_table(path,"chunks"))==len(chunks)

def test_forged_citations_rejected(corpus):
    with pytest.raises(ProviderError):validate_draft(Draft(status="answered",claims=[Claim(text="معلومة",source_ids=["invented"])]),corpus[0])
def test_answer_without_citations_rejected(corpus):
    with pytest.raises(ProviderError):validate_draft(Draft(status="answered"),corpus[0])
def test_csv_citation_has_no_fake_page(corpus):
    source=citation(next(c for c in corpus[0] if c["kind"]=="computer_engineering_courses"))
    assert source.page_start is None and source.record_id

def test_fusion():
    ranked=rrf([["a","b"],["b","c"]]);assert ranked[0]=="b"
def test_session_memory_is_user_only_and_bounded():
    sessions=Sessions();sid,history=sessions.get(None)
    for i in range(7):sessions.add(sid,str(i))
    assert sessions.get(sid)[1]==["3","4","5","6"]
    assert sessions.get("invented")[0]!="invented"
