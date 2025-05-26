from pydantic import BaseModel, RootModel
from typing import Optional, Dict, Any
from bson import ObjectId
from pydantic import validator
import datetime

from util.json_encoder import doc_encoder


class ConversationResponse(BaseModel):
   id: int
   doc_id: str
   source_ids: list[int]
   created_at: datetime.datetime
   topic : Optional[str] = ""
   
   class Config:
       from_attributes = True
       
       
class ConversationDetailResponse(ConversationResponse):
    doc: Optional[dict] = None  # 不仔细定义这个模型，让其能返回更多值
    
    class Config:
        json_encoders = {
            dict: doc_encoder
        }
        
class ConversationSourceUpdate(BaseModel):
    source_id : int
    source_name : str
    
class ChatTaskResponse(BaseModel):
    chat_id : str
    conversation_id : int
    conversation_doc_id : str
    source_doc_ids : str
    current_request : str
    
    
class ChatSSEResponse(BaseModel):
    chat_id : Optional[str] = ""
    role : Optional[str] = ""  # agent name
    status : Optional[str] = ""  # success, failed
    error : Optional[Any] = "" # error message
    content_type : Optional[str] = ""  # signal , message, thought_process/code/sql, data, chart
    content : Optional[Any] = "" 
    thought_process : Optional[Any] = ""
    

    