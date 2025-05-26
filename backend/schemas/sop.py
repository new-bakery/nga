from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from bson import ObjectId


class SOP_Step(BaseModel):
    step_number: int
    title: str
    description: str
    action: str
    examples: Optional[List[str]]  = []
    
    class Config:
       from_attributes = True
    
    
class SOP_Analysis_Guideline(BaseModel):
    title: str
    condition: str
    action: str
    reference_data : Optional[List[str]]  = []
    
    class Config:
       from_attributes = True
    

class SOP(BaseModel):
    id: Optional[str] = ""
    title: str
    description: str
    steps: List[SOP_Step]
    domains : Optional[List[str]]  = []
    tags: Optional[str] = ""
    is_disabled : bool = False
    analysis_guidelines: List[SOP_Analysis_Guideline]
    
    class Config:
       from_attributes = True
       arbitrary_types_allowed=True
       
class SOP_ListItem(BaseModel):
    id: str
    title: str
    description: str
    domains : Optional[List[str]]  = []
    tags: Optional[str] = ""
    is_disabled : bool = False

    class Config:
        from_attributes = True
