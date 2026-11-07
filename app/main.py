import secrets
import threading
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings, ROOT
from app.schemas import ChatRequest, ChatResponse, PlanRequest
from app.generation import ProviderError, ConfigurationError
from app.retrieval import Retriever
from app.service import Advisor
from app.planner import Planner

app=FastAPI(title="دليل — المرشد الأكاديمي",version="1.0.0")
router=APIRouter();cfg=settings();runtime_lock=threading.Lock();chat_slots=threading.BoundedSemaphore(2)

@lru_cache
def runtime():
    with runtime_lock:
        r=Retriever(cfg)
        return r,Advisor(r,cfg),Planner(r.courses,r.report)

def ready():
    try: return runtime()
    except RuntimeError as e: raise HTTPException(503,str(e)) from None

@router.get("/health")
def health():
    import json
    path=cfg.indexes/"active.json"
    manifest=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {"status":"ok","indexed":bool(manifest),"semantic":manifest.get("semantic",False),"chunks":manifest.get("chunks",0),
            "generation_configured":bool(cfg.gemini_api_key),"gemini_model":cfg.gemini_model,"scope":"الخطة المورّدة لهندسة الحاسوب — جامعة النجاح الوطنية"}

@router.post("/chat",response_model=ChatResponse)
def chat(request:ChatRequest,http_request:Request):
    if not cfg.gemini_api_key: raise HTTPException(503,"أضف GEMINI_API_KEY إلى ملف .env ثم أعد تشغيل الخادم.")
    if not chat_slots.acquire(blocking=False): raise HTTPException(429,"الخادم مشغول بطلبات أخرى. حاول بعد قليل.")
    try:
        from app.auth import store,COOKIE
        profile=None
        token=http_request.cookies.get(COOKIE)
        if token:
            try: profile=store().current(token)
            except HTTPException: raise HTTPException(401,"انتهت الجلسة. يرجى تسجيل الدخول مجدداً.") from None
        return ready()[1].chat(request,profile)
    except ConfigurationError as e: raise HTTPException(503,str(e)) from None
    except ProviderError as e: raise HTTPException(502,str(e)) from None
    except ValueError as e: raise HTTPException(422,str(e)) from None
    finally: chat_slots.release()

@router.get("/documents")
def documents(): return ready()[0].documents

@router.get("/documents/{document_id}")
def document(document_id:str):
    item=next((d for d in ready()[0].documents if d["document_id"]==document_id),None)
    if not item: raise HTTPException(404,"المستند غير موجود.")
    return item

@router.get("/documents/{document_id}/file")
def original_file(document_id:str):
    item=document(document_id)
    path=(cfg.data_dir/item["filename"]).resolve()
    if not path.is_relative_to(cfg.data_dir.resolve()) or path.suffix.lower()!=".pdf" or not path.is_file():
        raise HTTPException(404,"الملف غير متاح للعرض.")
    return FileResponse(path,media_type="application/pdf",content_disposition_type="inline",filename=path.name)

@router.get("/sources/{source_id}")
def source(source_id:str):
    c=ready()[0].by_id.get(source_id)
    if not c: raise HTTPException(404,"المصدر غير موجود.")
    from app.generation import citation
    return citation(c)

@router.get("/courses")
def courses(): return ready()[0].courses

@router.post("/planner")
def planner(request:PlanRequest):
    try: return ready()[2].plan(request.completed,request.proposed)
    except ValueError as e: raise HTTPException(422,str(e)) from None

@router.get("/inspection")
def inspection(): return ready()[0].report

@router.post("/documents/ingest")
def reindex(authorization:str|None=Header(default=None)):
    if not cfg.admin_token or not secrets.compare_digest(authorization or "","Bearer "+cfg.admin_token):
        raise HTTPException(403,"إعادة الفهرسة متاحة للمسؤول فقط.")
    from app.ingestion import ingest
    try:
        report=ingest(cfg)
        runtime.cache_clear()
        return {"status":"indexed","chunks":report["chunks"],"documents":report["documents"]}
    except RuntimeError as error:
        raise HTTPException(409,str(error)) from None

from app.auth import router as auth_router
app.include_router(auth_router,prefix="/api")
app.include_router(router,prefix="/api")
app.include_router(router,include_in_schema=False)
dist=ROOT/"frontend"/"dist"
if (dist/"assets").exists(): app.mount("/assets",StaticFiles(directory=dist/"assets"),name="assets")
if (dist/"fonts").exists(): app.mount("/fonts",StaticFiles(directory=dist/"fonts"),name="fonts")

@app.get("/",include_in_schema=False)
def home():
    if (dist/"index.html").exists(): return FileResponse(dist/"index.html")
    return JSONResponse({"message":"Build the frontend: cd frontend; npm install; npm run build", "api_docs":"/docs"})
