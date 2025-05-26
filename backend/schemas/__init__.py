from typing import Optional, Dict, Any
from pydantic import BaseModel

class SuccessOrErrorResponse(BaseModel):
    success: bool = False
    error: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Any] = None
    
    class Config:
        from_attributes = True
    
    
class TextRequestModel(BaseModel):
    text: str
    
    class Config:
        from_attributes = True