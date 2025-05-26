from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

# class Client(Base):
#     __tablename__ = "clients"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)
#     code = Column(String, unique=True, index=True)
#     expire = Column(DateTime, nullable=True)  # Null means never expires

#     # 反向关系：一个 Client 可能有多个 User
#     users = relationship("User", back_populates="client")

# TODO: Let's implement client concept later