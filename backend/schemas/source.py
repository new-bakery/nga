from pydantic import BaseModel, RootModel
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pydantic import validator

from util.json_encoder import doc_encoder



class LangDescriptionModel(BaseModel):
    lang : str
    text : str
    
    class Config:
        from_attributes = True
    
    
class ColumnModel(BaseModel):
    column_name : str
    type : str
    description : list[LangDescriptionModel]
    tags : str
    _signature : Optional[Any] = None
    class Config:
        from_attributes = True

    
    
class ForeignKeyModel(BaseModel):
    foreign_key_name : str
    primary_table : str
    primary_column : str
    foreign_table : str
    foreign_column : str
    by : str
    
    class Config:
        from_attributes = True
    
    
class EntitySchemaModel(BaseModel):
    table_name : str
    file_type : Optional[str] = ""
    original_file : Optional[str] = ""
    object_name : Optional[str] = ""
    sheet_name : Optional[str] = ""
    media_type : Optional[str] = ""
    shape : Optional[List] = []
    description : list[LangDescriptionModel]
    domains : list[str]
    tags: str
    columns : list[ColumnModel]
    primary_keys : list[str]
    foreign_keys : list[ForeignKeyModel]

    class Config:
        from_attributes = True


class SourceTypeResponse(BaseModel):
    name: str
    display_info: dict
    connection_info: dict
    
    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    doc_id: str
    source_name: Optional[str] = None
    source_type: str
    connection: Optional[dict] = None
    is_private: bool
    description: Optional[LangDescriptionModel] = None
    user_id: int
    status: dict

    class Config:
        from_attributes = True
        
        json_encoders = {
            ObjectId: str ,  # 将 ObjectId 自动转换为字符串
        }

        
class SourceDetailResponse(SourceResponse):
    doc: Optional[dict] = None  # 不仔细定义这个模型，让其能返回更多值
    
    class Config:
        json_encoders = {
            dict: doc_encoder
        }
        


class SourceCreateUpdate(BaseModel):
    source_name : str
    is_private : bool
    description : list[LangDescriptionModel]
    connection_info : dict
    additional_details : str
    entities : list[EntitySchemaModel]
     
    class Config:
        from_attributes = True


class SourceAnnotationRequest(BaseModel):
    lang : list[str]
    source_name: str
    source_description : list[LangDescriptionModel]
    entity : EntitySchemaModel
    
    class Config:
        from_attributes = True
    
    
class LangSourceAnnotationResponse(BaseModel):
    table_description: str
    columns : dict[str, str]
    
    class Config:
        from_attributes = True
    
    
class SourceAnnotationResponse(RootModel[Dict[str, LangSourceAnnotationResponse]]):
    pass
    
    class Config:
        from_attributes = True

