from pydantic import BaseModel
from typing import Optional

class ResumeRoastRequest(BaseModel):
    """
    Schema for resume roasting request with text input
    """
    resume_text: str
    roast_style: Optional[str] = "funny"  # funny, professional, brutal, constructive
    
class ResumeRoastResponse(BaseModel):
    """
    Schema for resume roasting response
    """
    roast: str
    style: str
    suggestions: Optional[list] = []
    confidence_score: Optional[float] = None
    
class FileUploadResponse(BaseModel):
    """
    Schema for file upload response
    """
    filename: str
    file_type: str
    extracted_text: str
    message: str

# Export schemas
__all__ = [
    "ResumeRoastRequest", 
    "ResumeRoastResponse", 
    "FileUploadResponse"
]