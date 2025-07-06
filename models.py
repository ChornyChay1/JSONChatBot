from pydantic import BaseModel
from typing import Optional, Dict, List

class Question(BaseModel):
    question: str
    type: str
    options: list[str] = []
    correct_answer: str | None = None
    next_id: str | None = None
    audio_file: str | None = None
    video_file: str | None = None
    image_file: str | None = None
    addictional_images: list[str] = []
    branches: Optional[Dict[str, str]] = None
    branching: bool = False 
    is_photo: bool = False

