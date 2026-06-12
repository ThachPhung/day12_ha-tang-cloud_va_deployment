from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    daily_new_limit: int
    daily_review_limit: int
    timezone: str
    sound_enabled: bool
    theme: str

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    daily_new_limit: int | None = Field(None, ge=1, le=500)
    daily_review_limit: int | None = Field(None, ge=1, le=1000)
    timezone: str | None = None
    sound_enabled: bool | None = None
    theme: str | None = None
