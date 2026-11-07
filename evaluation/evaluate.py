"""Offline retrieval evaluation by annotated evidence groups; --live explicitly calls Gemini."""
import argparse
import json
import statistics
import time
from datetime import datetime,timezone
from pathlib import Path
from app.config import settings,ROOT
from app.retrieval import Retriever
from app.generation import Generator

def matches(chunk,rule):return all(chunk.get(key)==value for key,value in rule.items())
def run(split="reference",live=False):
    cfg=settings();r=Retriever(cfg)
    cases=json.loads((ROOT/"evaluation"/f"{split}_cases.json").read_text(encoding="utf-8"))
    results=[]
    for case in cases:
        query="\n".join(case.get("history",[])+[case["question"]])
        row={"id":case["id"],"category":case["category"],"question":case["question"],"expected_status":case["expected_status"]}
        groups=case["evidence_groups"]
        for mode in ["lexical","hybrid"]:
            start=time.perf_counter();hits=r.retrieve(query,mode=mode)
            coverage=[any(any(matches(chunk,rule) for rule in alternatives) for chunk in hits) for alternatives in groups]
            first=next((i+1 for i,c in enumerate(hits) if any(matches(c,rule) for group in groups for rule in group)),None)
            row[mode]={"evidence_group_recall_at_k":sum(coverage)/len(coverage) if coverage else None,
                       "reciprocal_rank":1/first if first else (0 if groups else None),"seconds":round(time.perf_counter()-start,3),
                       "retrieved":[{"id":c["source_id"],"kind":c["kind"],"page":c["page_start"],"record":c["record_key"]} for c in hits]}
        if live:
            start=time.perf_counter()
            try:
                answer=Generator(cfg).generate(case["question"],r.retrieve(query),case.get("history",[]),"formal",r.report)
                row["generation"]={**answer,"sources":[s.model_dump() for s in answer["sources"]],"seconds":round(time.perf_counter()-start,3),
                    "status_matches":answer["status"]==case["expected_status"],"correctness_manual_review":None,"groundedness_manual_review":None}
            except Exception as e:row["generation"]={"error":str(e),"status_matches":False}
        results.append(row)
        print(case["id"],{m:row[m]["evidence_group_recall_at_k"] for m in ["lexical","hybrid"]},flush=True)
    summary={}
    for mode in ["lexical","hybrid"]:
        scored=[row[mode]["evidence_group_recall_at_k"] for row in results if row[mode]["evidence_group_recall_at_k"] is not None]
        summary[mode]={"mean_evidence_group_recall_at_k":statistics.mean(scored) if scored else None,
                       "scored_questions":len(scored),"k":cfg.retrieval_k}
    report={"split":split,"created_at":datetime.now(timezone.utc).isoformat(),"semantic_index":r.manifest["semantic"],
            "summary":summary,"live_generation":live,"results":results,
            "limitations":["Evidence groups identify document pages/records, not every relevant chunk.",
                           "Lexical baseline includes the same exact-code and documented conflict routing as hybrid.",
                           "No answer correctness or refusal score is established by retrieval alone.",
                           "LLM support checking is not a guarantee; manual review is still required."]}
    target=ROOT/"evaluation"/"reports";target.mkdir(exist_ok=True)
    name=f"{split}{'-live' if live else ''}.json"
    (target/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--split",choices=["reference","held_out","fresh"],default="reference");p.add_argument("--live",action="store_true",help="Makes metered Gemini requests; requires a local key")
    args=p.parse_args();run(args.split,args.live)
