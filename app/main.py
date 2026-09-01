import json
import os
import time
import uuid

import pymupdf
import redis
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


# r = redis.Redis(host="localhost", port=6379, decode_responses=True)
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

QUEUE_NAME = "render_demo_queue"


@app.post("/jobs")
def create_job(email: str):
    """
    Simulates: 'user signs up -> we need to send a welcome email'.
    The web service does NOT send the email itself — that would block
    the request. It just enqueues a job and returns instantly.
    """
    job_id = str(uuid.uuid4())[:8]
    job = {
        "id": job_id,
        "type": "send_welcome_email",
        "email": email,
        "enqueued_at": time.time(),
    }
    r.rpush(QUEUE_NAME, json.dumps(job))
    return {"status": "queued", "job_id": job_id, "queue_length": r.llen(QUEUE_NAME)}


@app.get("/status/{job_id}")
def job_status(job_id: str):
    """Worker writes results here (a Redis hash) once it finishes a job."""
    result = r.hget("render_demo_results", job_id)
    if result is None:
        return {"job_id": job_id, "status": "pending_or_unknown"}
    return json.loads(result)
