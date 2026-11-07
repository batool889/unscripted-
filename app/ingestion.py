"""Page-aware, provenance-preserving ingestion; runtime never indexes project instructions."""
import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from app.arabic import normalize
from app.config import settings
from app.embedding import Embedder
from app.storage import build_db, VectorStore

EVIDENCE_CSV = {"computer_engineering_courses.csv", "prerequisites.csv", "degree_requirements.csv", "academic_faq.csv", "academic_rules.csv"}
EXCLUDED = {"README.md", "README.txt", "collection_gaps.csv", "source_registry.csv"}
LABELS = {
 "course_code":"رمز المساق", "course_name_ar":"اسم المساق", "course_name_en":"الاسم بالإنجليزية",
 "credit_hours":"الساعات المعتمدة", "requirement_group":"فئة المتطلب", "prerequisite_expression":"المتطلب السابق",
 "eligibility_note":"تنبيه", "prerequisite_review_status":"حالة مراجعة المتطلب", "review_status":"حالة المراجعة",
 "question_en":"السؤال", "answer_ar_summary":"ملخص الإجابة", "topic":"الموضوع",
 "requirement":"المتطلب", "credits":"الساعات", "rule_id":"معرف القاعدة", "value":"القيمة",
 "scope":"النطاق", "authority":"نوع المصدر", "notes":"ملاحظات", "status":"حالة التحقق", "review_note":"ملاحظة المراجعة",
}
DISPLAY = {"computer_engineering_courses":"جدول مساقات هندسة الحاسوب", "prerequisites":"جدول المتطلبات السابقة",
 "degree_requirements":"متطلبات خطة هندسة الحاسوب", "academic_faq":"ملخص الأسئلة الشائعة", "academic_rules":"قواعد أكاديمية منقولة"}


def sha(data): return hashlib.sha256(data).hexdigest()
def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def discover(data):
    return sorted([p for p in data.rglob("*") if p.is_file() and not any(x in {"processed", "indexes"} for x in p.relative_to(data).parts)
                   and (p.suffix.lower()==".pdf" or p.name in EVIDENCE_CSV)],key=lambda p:str(p))

def split_text(text, tokenizer, maximum=400, overlap=50):
    """Split at sentence/newline boundaries when possible, retaining exact original substrings."""
    encoded=tokenizer(text,return_offsets_mapping=True,add_special_tokens=False)
    offsets=encoded["offset_mapping"]
    start=0
    while start<len(offsets):
        end=min(start+maximum,len(offsets))
        char_start=offsets[start][0];char_end=offsets[end-1][1]
        if end<len(offsets):
            substring=text[char_start:char_end]
            boundary=max(substring.rfind("\n"),substring.rfind(". "),substring.rfind("؛"))
            if boundary>len(substring)*0.65:
                wanted=char_start+boundary+1
                while end>start+1 and offsets[end-1][1]>wanted: end-=1
                char_end=offsets[end-1][1]
        piece=text[char_start:char_end].strip()
        if piece: yield piece
        if end==len(offsets): break
        start=max(start+1,end-overlap)


def page_label(text):
    for line in text.splitlines()[:8]:
        value=line.strip()
        if re.fullmatch(r"[0-9٠-٩]{1,3}",value): return value
    return None


def pdf_sections(text):
    # Keep entire page when no explicit numbered article is detected. No inferred article IDs.
    matches=list(re.finditer(r"(?m)^[^\n]*(?:\)\s*([0-9٠-٩]+)\s*\(\s*المـ*ادة|(?:المـ*ادة|مادة)\s*[:(]\s*([0-9٠-٩]+))",text))
    if not matches: return [(text,None)]
    result=[]
    if text[:matches[0].start()].strip(): result.append((text[:matches[0].start()],None))
    for i,m in enumerate(matches):
        result.append((text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)],(m.group(1) or m.group(2))))
    return result


def collect(cfg,embedder):
    import pymupdf
    files=discover(cfg.data_dir)
    if not files: raise RuntimeError("No academic PDF/CSV files found in data/.")
    registry={}
    for p in cfg.data_dir.rglob("source_registry.csv"):
        for r in read_csv(p): registry[r.get("source_id","")]=r
    documents=[];chunks=[];courses=[];requirements=[];pages=[];warnings=[];conflicts=[]
    seen=set();all_prereqs={}
    for p in files:
        raw_hash=sha(p.read_bytes())
        if raw_hash in seen: continue
        seen.add(raw_hash)
        rel=p.relative_to(cfg.data_dir).as_posix()
        doc_id=p.stem+"-"+sha(rel.encode())[:8]
        doc={"document_id":doc_id,"document_name":DISPLAY.get(p.stem,p.name),"filename":rel,"content_hash":raw_hash,
             "institution":"جامعة النجاح الوطنية","program":"هندسة الحاسوب","version":"غير محددة",
             "verification_status":"supplied_extraction_not_independently_verified","source_url":"","chunks":0}
        if p.suffix.lower()==".pdf":
            doc["document_name"]="دليل الطالب — جامعة النجاح الوطنية"
            doc["source_url"]=registry.get("student_guide_2026_27",{}).get("url","")
            with pymupdf.open(p) as pdf:
                doc["page_count"]=len(pdf)
                first="\n".join(pdf[i].get_text(sort=False) for i in range(min(3,len(pdf))))
                if "2027" in first and "2026" in first: doc["version"]="2026–2027"
                doc["verification_status"]="official_pdf_supplied"
                for n,page in enumerate(pdf,start=1):
                    text=page.get_text(sort=False).strip()
                    pages.append({"document_id":doc_id,"page":n,"text":text})
                    label=page_label(text)
                    if len(re.findall(r"[\u0621-\u064a]",text))<25:
                        warnings.append({"document":rel,"page":n,"issue":"صفحة قليلة النص؛ صورة أو فاصل، وقد تحتاج OCR"})
                        continue
                    # Numeric table rows extracted as concatenated digits are not valid evidence.
                    dense=("البرنامج" in text and "إجباري" in text and "اختياري" in text) or (bool(re.search(r"\d{7,}",normalize(text))) and "البرنامج" in text)
                    if dense:
                        warnings.append({"document":rel,"page":n,"issue":"جدول رقمي يحتاج مراجعة؛ مستبعد من البحث لمنع قراءة أعمدة مدمجة"})
                        continue
                    for line in text.splitlines():
                        if "هندسة الحاسوب" in normalize(line):
                            nums=re.findall(r"(?<!\d)1[3-9]\d(?!\d)",normalize(line))
                            if nums: conflicts.append({"type":"degree_total_candidate","value":int(nums[-1]),"document_id":doc_id,"page":n,"excerpt":line.strip()})
                    for section_index,(section,article) in enumerate(pdf_sections(text)):
                        title=next((ln.strip() for ln in section.splitlines() if len(ln.strip())>8),doc["document_name"])
                        parent=f"{doc_id}:p{n}:s{section_index}"
                        for j,piece in enumerate(split_text(section,embedder.tokenizer,cfg.chunk_tokens,cfg.chunk_overlap)):
                            search=normalize("\n".join(line for line in piece.splitlines() if not (("دليل الطالب" in normalize(line) and re.search(r"202[67]",line)) or "An-Najah" in line or re.fullmatch(r"\s*[0-9٠-٩]{1,3}\s*",line))))
                            # Normalization must also fit the real embedding tokenizer.
                            if embedder.count("passage: "+search)>512: raise ValueError(f"Oversized chunk {parent}")
                            chunks.append({"source_id":f"{parent}:c{j}","document_id":doc_id,"document_name":doc["document_name"],
                               "text":piece,"search_text":search,"page_start":n,"page_end":n,"printed_page":label,
                               "article_number":article,"record_id":None,"section_title":title[:160],"parent_section_id":parent,
                               "parent_text":section,"source_url":doc["source_url"],"version":doc["version"],
                               "verification_status":doc["verification_status"],"institution":"nnu","program":"general",
                               "kind":"pdf","record_key":""})
        else:
            rows=read_csv(p)
            doc["rows"]=len(rows)
            doc["version"]="الخطة المورّدة؛ سنة السريان غير مثبتة" if p.name in {"computer_engineering_courses.csv","prerequisites.csv","degree_requirements.csv"} else "ملخص يحتاج مطابقة الدليل"
            for i,row in enumerate(rows,start=2):
                if p.name=="academic_rules.csv" and "user" in row.get("authority",""): continue
                if p.name=="computer_engineering_courses.csv":
                    row=dict(row);row["source_document_id"]=doc_id;row["source_record_id"]=f"row:{i}"
                    courses.append(row)
                if p.name=="prerequisites.csv": all_prereqs[row["course_code"]]=row
                if p.name=="degree_requirements.csv": requirements.append(row)
                excluded={"source_url","minimum_passing_grade","grading_scheme","passing_status_required","source_document_id","source_record_id","academic_year_selection"}
                text="\n".join(f"{LABELS.get(k,k)}: {v}" for k,v in row.items() if v and k not in excluded)
                # These remain attributed derived data, never silently promoted to verified original policy.
                status=row.get("status",row.get("prerequisite_review_status",row.get("review_status",row.get("authority","supplied_csv"))))
                url=row.get("source_url","");doc["source_url"]=doc["source_url"] or url
                key=row.get("course_code",row.get("requirement",row.get("topic",row.get("rule_id",str(i)))))
                for j,piece in enumerate(split_text(text,embedder.tokenizer,cfg.chunk_tokens,cfg.chunk_overlap)):
                    chunks.append({"source_id":f"{doc_id}:r{i}:c{j}","document_id":doc_id,"document_name":doc["document_name"],
                         "text":piece,"search_text":normalize(piece),"page_start":None,"page_end":None,"printed_page":None,
                         "article_number":None,"record_id":f"row:{i}","record_key":key,"section_title":row.get("course_name_ar",key),
                         "parent_section_id":f"{doc_id}:r{i}","parent_text":text,"source_url":url,"version":doc["version"],
                         "verification_status":status,"institution":"nnu","program":"computer_engineering","kind":p.stem})
        doc["chunks"]=sum(c["document_id"]==doc_id for c in chunks)
        documents.append(doc)
    # Reject contradictory extracted prerequisite tables instead of choosing silently.
    for course in courses:
        other=all_prereqs.get(course["course_code"])
        if other and other["prerequisite_expression"].strip()!=course["prerequisite_expression"].strip():
            course["prerequisite_review_status"]="conflicting_extractions"
            warnings.append({"course":course["course_code"],"issue":"تعارض بين ملفي المتطلبات؛ يلزم تدقيق"})
    codes=[c["course_code"] for c in courses]
    if len(codes)!=len(set(codes)): raise ValueError("Duplicate course codes in catalog")
    totals=[int(r["credits"]) for r in requirements if r["requirement"]=="total_credit_hours"]
    degree_conflicts=[c for c in conflicts if totals and c["value"]!=totals[0]]
    if degree_conflicts:
        warnings.append({"issue":"تعارض إجمالي الساعات بين الدليل والخطة الموردة","plan_total":totals[0],"guide_evidence":degree_conflicts})
    report={"documents":len(documents),"chunks":len(chunks),"courses":len(courses),"warnings":warnings,
            "degree_conflicts":degree_conflicts,"excluded_files":sorted(EXCLUDED),"requirements":requirements,
            "created_at":datetime.now(timezone.utc).isoformat()}
    return chunks,courses,documents,report,pages


def ingest(cfg=None,lexical_only=False):
    cfg=cfg or settings();cfg.processed.mkdir(parents=True,exist_ok=True);cfg.indexes.mkdir(parents=True,exist_ok=True)
    lock=cfg.indexes/"ingest.lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise RuntimeError("Another ingestion is running. Remove data/indexes/ingest.lock only after checking no ingestion is active.")
    os.close(fd)
    try:
        embedder=Embedder(cfg)
        identity=embedder.identity()
        signature={"pipeline":"v3", "identity":identity,"semantic":not lexical_only,
                   "files":{p.relative_to(cfg.data_dir).as_posix():sha(p.read_bytes()) for p in discover(cfg.data_dir)}}
        digest=sha(json.dumps(signature,sort_keys=True).encode())[:20]
        manifest_path=cfg.indexes/"active.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text())["generation"]==digest:
            print("Index already current.");return json.loads((cfg.processed/"inspection.json").read_text(encoding="utf-8"))
        chunks,courses,documents,report,pages=collect(cfg,embedder)
        collection="academic_"+digest
        if not lexical_only:
            store=VectorStore(cfg.indexes/"chroma",collection,create=True)
            cache_dir=cfg.indexes/"embedding_cache";cache_dir.mkdir(exist_ok=True)
            for start in range(0,len(chunks),32):
                batch=chunks[start:start+32];vectors=[None]*len(batch);missing=[]
                for i,c in enumerate(batch):
                    key=sha((json.dumps(identity,sort_keys=True)+c["search_text"]).encode())
                    cache=cache_dir/(key+".json")
                    if cache.exists(): vectors[i]=json.loads(cache.read_text())
                    else: missing.append((i,cache))
                if missing:
                    encoded=embedder.encode([batch[i]["search_text"] for i,_ in missing])
                    for (i,cache),vector in zip(missing,encoded):
                        vectors[i]=vector;cache.write_text(json.dumps(vector),encoding="utf-8")
                store.upsert(batch,vectors)
                print(f"Indexed {min(start+32,len(chunks))}/{len(chunks)} chunks",flush=True)
        db_path=cfg.indexes/(digest+".sqlite")
        build_db(db_path,chunks,courses,documents,{"report":report,"embedding":identity})
        (cfg.processed/"inspection.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        (cfg.processed/"pages.json").write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding="utf-8")
        (cfg.processed/"sample_chunks.json").write_text(json.dumps(chunks[:8],ensure_ascii=False,indent=2),encoding="utf-8")
        manifest={"generation":digest,"database":db_path.name,"collection":collection,"embedding":identity,"semantic":not lexical_only,"chunks":len(chunks)}
        temp=manifest_path.with_suffix(".tmp");temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8");os.replace(temp,manifest_path)
        print(json.dumps({k:report[k] for k in ["documents","chunks","courses","degree_conflicts"]},ensure_ascii=False,indent=2))
        return report
    finally: lock.unlink(missing_ok=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--lexical-only",action="store_true",help="Explicit diagnostic mode; not semantic RAG")
    args=parser.parse_args();ingest(lexical_only=args.lexical_only)
