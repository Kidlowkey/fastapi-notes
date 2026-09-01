import time

import anthropic
import pymupdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Extraction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

anthropic_client = anthropic.Anthropic()

MAX_QUESTIONS = 10

QUESTIONS_TOOL = {
    "name": "submit_questions",
    "description": "Submit the generated comprehension questions for the document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": f"Up to {MAX_QUESTIONS} high-quality, relevant, contextual questions about the document.",
                "items": {"type": "string"},
                "maxItems": MAX_QUESTIONS,
            },
        },
        "required": ["questions"],
    },
}


def generate_questions(text: str) -> list[str]:
    message = anthropic_client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[QUESTIONS_TOOL],
        tool_choice={"type": "tool", "name": "submit_questions"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Generate up to 10 high-quality, relevant, and contextual questions "
                    "about the following document. The questions should test genuine "
                    "understanding of the document's specific content, not generic "
                    "reading-comprehension filler.\n\n"
                    f"<document>\n{text}\n</document>"
                ),
            }
        ],
    )

    for block in message.content:
        if block.type == "tool_use" and block.name == "submit_questions":
            questions = block.input.get("questions", [])
            return list(questions)[:MAX_QUESTIONS]

    return []


@app.get("/")
def root():
    return {"message": "Extraction is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    total_start = time.perf_counter()

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    upload_start = time.perf_counter()
    contents = await file.read()
    upload_seconds = time.perf_counter() - upload_start

    try:
        doc = pymupdf.open(stream=contents, filetype="pdf")
    except pymupdf.FileDataError:
        raise HTTPException(status_code=400, detail="Could not read PDF file")

    extraction_start = time.perf_counter()

    pages = []

    for page in doc:
        pages.append(page.get_text())

    text = "\n".join(pages)

    extraction_seconds = time.perf_counter() - extraction_start

    doc.close()

    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in PDF")

    question_generation_start = time.perf_counter()
    try:
        questions = generate_questions(text)
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Question generation failed: {exc}")
    question_generation_seconds = time.perf_counter() - question_generation_start

    total_seconds = time.perf_counter() - total_start

    return {
        "filename": file.filename,
        "questions": questions,
        "timings": {
            "upload_seconds": upload_seconds,
            "extraction_seconds": extraction_seconds,
            "question_generation_seconds": question_generation_seconds,
            "total_seconds": total_seconds,
        },
    }
