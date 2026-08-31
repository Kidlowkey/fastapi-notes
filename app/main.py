import time

import pymupdf
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Extraction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Extraction is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()

    try:
        doc = pymupdf.open(stream=contents, filetype="pdf")
    except pymupdf.FileDataError:
        raise HTTPException(status_code=400, detail="Could not read PDF file")

    start = time.perf_counter()

    pages = []

    for page in doc:
        pages.append(page.get_text())

    text = "\n".join(pages)

    extraction_seconds = time.perf_counter() - start

    doc.close()

    return {
        "filename": file.filename,
        "text": text,
        "extraction_seconds": extraction_seconds,
    }