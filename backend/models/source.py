from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime
from pydantic import validator
import bson
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import JSON

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    doc_id = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # excel, mysql, postgresql, etc
    is_private = Column(Boolean, default=True)  # 是否私有
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # id of the user
    status = Column(MutableDict.as_mutable(JSON), nullable=True)  # 状态信息
    
    # NOTICE: Sourece_Name 不在此表中保存，所以其实Source Name是可以重复的
    
    user = relationship("User", back_populates="sources") 
    
    @validator('doc_id')
    def validate_objectid(cls, v):
        if len(v) != 24 or not bson.ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId format')
        return v