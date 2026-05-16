"""Simple persistent note store."""

import json
import os
from datetime import datetime

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.json")


def _load() -> list[dict]:
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        return json.load(f)


def _save(notes: list[dict]) -> None:
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


def add(text: str, tags: list[str] | None = None) -> dict:
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "text": text,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    notes.append(note)
    _save(notes)
    return note


def list_all() -> list[dict]:
    return _load()


def search(keyword: str) -> list[dict]:
    """Return notes whose text contains *keyword* (case-insensitive)."""
    # TODO: extend to also search within tags
    keyword_lower = keyword.lower()
    return [n for n in _load() if keyword_lower in n["text"].lower()]


def delete(note_id: int) -> bool:
    notes = _load()
    updated = [n for n in notes if n["id"] != note_id]
    if len(updated) == len(notes):
        return False
    _save(updated)
    return True


# TODO: add export_to_markdown(filepath) – write each note as a ## heading
#       with its tags listed below, so users can keep a human-readable archive.

def filter_by_tag(tag: str) -> list[dict]:
    """Return notes that include *tag* (case-insensitive)."""
    tag_lower = tag.lower()
    return [n for n in _load() if any(t.lower() == tag_lower for t in n["tags"])]
