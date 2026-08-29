from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Notes API", version="1.0.0")


class NoteIn(BaseModel):
    text: str
    done: bool = False


class Note(NoteIn):
    id: UUID = Field(default_factory=uuid4)


notes: list[Note] = []


@app.get("/")
def root():
    return {"message": "Notes API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/notes")
def list_notes():
    return notes


@app.get("/notes/{note_id}")
def get_note(note_id: UUID):
    for note in notes:
        if note.id == note_id:
            return note
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")


@app.post("/notes", status_code=status.HTTP_201_CREATED)
def create_note(note_in: NoteIn):
    note = Note(text=note_in.text, done=note_in.done)
    notes.append(note)
    return {**note.model_dump()}


@app.put("/notes/{note_id}")
def update_note(note_id: UUID, note_in: NoteIn):
    for note_index, note in enumerate(notes):
        if note.id == note_id:
            notes[note_index] = Note(id=note_id, text=note_in.text, done=note_in.done)
            return notes[note_index]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")


@app.delete("/notes/{note_id}")
def delete_note(note_id: UUID):
    for note_index, note in enumerate(notes):
        if note.id == note_id:
            _ = notes.pop(note_index)

    return {"message": "Note deleted successfully"}
