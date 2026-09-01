import pymupdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

_ = load_dotenv()

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

    pages = []
    for page in doc:
        pages.append(page.get_text())

    text = "\n".join(pages)
    doc.close()

    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in PDF")

    return {"filename": file.filename, "text": text}
