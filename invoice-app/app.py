import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from invoice_extractor import extract_invoice_data
from invoice_pdf import generate_invoice_pdf

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


app = FastAPI(title="請求書変換アプリ")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    markup_type: str = Form(...),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="対応ファイル形式：JPG / PNG / GIF / WebP / PDF",
        )

    if markup_type not in ("20", "40", "kanri"):
        raise HTTPException(status_code=400, detail="markup_type が不正です")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="ファイルサイズは20MB以下にしてください")

    try:
        invoice_data = extract_invoice_data(content, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ抽出エラー: {str(e)}")

    try:
        pdf_path = generate_invoice_pdf(invoice_data, markup_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成エラー: {str(e)}")

    background_tasks.add_task(os.unlink, pdf_path)

    client_name = invoice_data.get("client_name", "invoice")
    safe_name = "".join(c for c in client_name if c.isalnum() or c in "ー_-") or "invoice"
    filename = f"請求書_{safe_name}.pdf"

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        background=background_tasks,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
