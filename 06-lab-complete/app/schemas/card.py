from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CardCreate(BaseModel):
    front: str = Field(min_length=1, max_length=255)
    back: str = Field(min_length=1)
    phonetic: str | None = None
    part_of_speech: str | None = None
    example: str | None = None
    example_translation: str | None = None
    notes: str | None = None
    tags: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    allow_duplicate: bool = False

    @field_validator("front", "back")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace only")
        return v


class CardUpdate(BaseModel):
    front: str | None = Field(None, min_length=1, max_length=255)
    back: str | None = Field(None, min_length=1)
    phonetic: str | None = None
    part_of_speech: str | None = None
    example: str | None = None
    example_translation: str | None = None
    notes: str | None = None
    tags: str | None = None
    image_url: str | None = None
    audio_url: str | None = None


class CardResponse(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    phonetic: str | None
    part_of_speech: str | None
    example: str | None
    example_translation: str | None
    notes: str | None
    tags: str | None
    image_url: str | None
    audio_url: str | None
    status: str | None = None
    due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImportPreviewRow(BaseModel):
    row_number: int
    front: str
    back: str
    phonetic: str | None = None
    part_of_speech: str | None = None
    example: str | None = None
    example_translation: str | None = None
    tags: str | None = None
    is_valid: bool
    is_duplicate: bool = False
    error: str | None = None


class ImportPreviewResponse(BaseModel):
    valid_count: int
    invalid_count: int
    duplicate_count: int
    rows: list[ImportPreviewRow]


class ImportConfirmRequest(BaseModel):
    rows: list[dict]
    skip_duplicates: bool = True
