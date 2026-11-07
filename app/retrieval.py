import json
import re
from collections import defaultdict
from functools import cached_property
import numpy as np
from rank_bm25 import BM25Okapi
from app.arabic import tokens, normalize, search_variants
from app.embedding import Embedder
from app.ingestion import split_text
from app.storage import load_table, VectorStore


def rrf(rankings,constant=60):
    scores=defaultdict(float)
    for ranked in rankings:
        for rank,key in enumerate(dict.fromkeys(ranked),start=1): scores[key]+=1/(constant+rank)
    return sorted(scores,key=lambda key:(-scores[key],key))

class Retriever:
    def __init__(self,cfg):
        self.cfg=cfg
        active=cfg.indexes/"active.json"
        if not active.exists(): raise RuntimeError("قاعدة المعرفة غير جاهزة. شغّل python -m app.ingestion أولاً.")
        self.manifest=json.loads(active.read_text(encoding="utf-8"))
        self.path=cfg.indexes/self.manifest["database"]
        self.chunks=load_table(self.path,"chunks")
        self.by_id={c["source_id"]:c for c in self.chunks}
        self.courses=load_table(self.path,"courses")
        self.documents=load_table(self.path,"documents")
        meta=load_table(self.path,"meta");self.report=next(m for m in meta if "requirements" in m)
        self.bm25=BM25Okapi([tokens(c["search_text"]) or ["__empty__"] for c in self.chunks])
        self.embedder=Embedder(cfg.model_copy(update={"embedding_revision":self.manifest["embedding"].get("resolved_revision") or cfg.embedding_revision}))
        if self.manifest["embedding"]["model"]!=cfg.embedding_model or self.manifest["embedding"]["revision"]!=cfg.embedding_revision:
            raise RuntimeError("تغيّر نموذج التضمين. أعد الفهرسة قبل تشغيل البحث.")
    @cached_property
    def vectors(self): return VectorStore(self.cfg.indexes/"chroma",self.manifest["collection"])
    def retrieve(self,question,k=None,mode="hybrid"):
        k=k or self.cfg.retrieval_k
        rankings=[];bm_scores={}
        variants=search_variants(question)
        for q in variants:
            scores=self.bm25.get_scores(tokens(q))
            order=[int(i) for i in np.argsort(-scores)[:self.cfg.candidate_k] if scores[i]>0]
            rankings.append([self.chunks[i]["source_id"] for i in order])
            for i in order: bm_scores[self.chunks[i]["source_id"]]=float(scores[i])
        if mode!="lexical" and self.manifest["semantic"]:
            # Long queries are searched in complete windows, not silently truncated.
            for q in variants:
                windows=list(split_text(normalize(q),self.embedder.tokenizer,400,20))
                for vector in self.embedder.encode(windows,kind="query"):
                    rankings.append([key for key,_ in self.vectors.query(vector,self.cfg.candidate_k)])
        exact=[]
        codes=set(re.findall(r"\b\d{8}\b",normalize(question)))
        for c in self.chunks:
            if c["record_key"] in codes and c["kind"] in {"computer_engineering_courses","prerequisites"}: exact.append(c["source_id"])
        if exact: rankings.extend([exact,exact])
        q=normalize(question)
        degree=any(t in q for t in ["تخرج","اتخرج","graduat","مجموع ساعات","مجموع الساعات","اجمالي ساعات","اجمالي الساعات"])
        if degree:
            degree_ids=[c["source_id"] for c in self.chunks if c["kind"]=="degree_requirements"]
            for conflict in self.report.get("degree_conflicts",[]):
                degree_ids.extend(c["source_id"] for c in self.chunks if c["document_id"]==conflict["document_id"] and c["page_start"]==conflict["page"])
            rankings.extend([degree_ids,degree_ids])
        ranked=rrf(rankings)
        # Exact course records and known degree conflicts must survive the context limit.
        forced=exact[:4] if exact else []
        if degree:
            forced=[c["source_id"] for c in self.chunks if c["kind"]=="degree_requirements" and c["record_key"]=="total_credit_hours"]
            for conflict in self.report.get("degree_conflicts",[]):
                forced.extend(c["source_id"] for c in self.chunks if c["document_id"]==conflict["document_id"] and c["page_start"]==conflict["page"])
        selected=[];parents=set()
        for key in dict.fromkeys(forced+ranked):
            c=self.by_id[key]
            parent=c["parent_section_id"]
            if parent in parents: continue
            parents.add(parent)
            if len(c["parent_text"])<=6500:
                c={**c,"text":c["parent_text"]}
            selected.append(c)
            if len(selected)>=k: break
        return selected
