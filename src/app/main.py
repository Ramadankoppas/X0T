import os
import shutil
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.pdf_service import process_and_index_pdf
from app.services.rag_service import generate_rag_stream

app = FastAPI(title="X0T Operations Agent", version="1.0.0")

# إنشاء مجلد مؤقت لحفظ ملفات الـ PDF المرفوعة
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Static files
BASE_DIR = Path(__file__).resolve().parent
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# 1. Endpoint لخدمة واجهة الـ Frontend
@app.get("/")
async def serve_frontend():
    static_file = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(static_file)


# 2. Endpoint لرفع ملف الـ PDF وتقطيعه وتخزينه في pgvector
@app.post("/api/v1/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="عذراً، يجب إرفاق ملف صيغته PDF فقط.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # حفظ الملف مؤقتاً على القرص
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # معالجة وتقطيع الـ PDF وتخزينه في PostgreSQL / pgvector
        await process_and_index_pdf(file_path)
        return {
            "status": "success",
            "message": f"تم رفع الملف بنجاح",
            "filename": file.filename
        }
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء معالجة الملف: {str(e)}")
    finally:
        # إزالة الملف المؤقت للحفاظ على مساحة السيرفر
        if os.path.exists(file_path):
            os.remove(file_path)


# 3. Endpoint للبحث والرد التدفق عبر SSE
@app.get("/api/v1/chat/stream")
async def chat_stream(request: Request, prompt: str):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="يرجى إدخال نص السؤال.")

    return StreamingResponse(
        generate_rag_stream(request, prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # منع Nginx/Coolify من عمل Buffering لـ SSE
        }
    )