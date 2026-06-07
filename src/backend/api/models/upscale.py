from pydantic import BaseModel
from typing import Optional
from backend.models.upscale import UpscaleMode

class UpscaleRequest(BaseModel):
    image: str  # Base64 encoded image
    upscale_mode: UpscaleMode = UpscaleMode.normal
    strength: Optional[float] = 0.3
