# AI assisted development
from pydantic import BaseModel
from datetime import datetime

class ConversionResponse(BaseModel):
    id: int
    original_filename: str
    original_path: str
    converted_path: str
    conversion_type: str
    timestamp: datetime

    class Config:
        from_attributes = True
