from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.adv import AdvStatus


class AdvertisementCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    desc: str = Field(min_length=10, max_length=4000)
    audience: str = Field(default="General audience", max_length=300)
    objective: str = Field(default="Awareness", max_length=80)
    platform: str = Field(default="Instagram Reels", max_length=80)
    aspect_ratio: str = Field(default="9:16", pattern="^(9:16|16:9|1:1)$")
    language: str = Field(default="en", max_length=16)
    tone: str = Field(default="Cinematic", max_length=80)
    cta: str = Field(default="", max_length=200)


class AdvertisementResponse(BaseModel):
    run_id: str
    name: str
    desc: str
    status: AdvStatus
    final_video_uri: Optional[str]
    created_at: datetime
    updated_at: datetime


class AdvertisementCreateResponse(BaseModel):
    run_id: str
    status: AdvStatus


class AdvertisementStatusResponse(BaseModel):
    run_id: str
    status: AdvStatus
    crew_status: Optional[dict]  # Full crew API status object


class VideoUrlResponse(BaseModel):
    video_url: str


class AdvertisementUpdate(BaseModel):
    status: Optional[AdvStatus] = None
    final_video_uri: Optional[str] = None
