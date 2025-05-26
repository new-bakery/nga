from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)  # # TODO: Let's implement client concept later
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")  # Can be 'user' or 'admin' for now. TODO: can be designed more flexible
    
    # client = relationship("Client", back_populates="users")  # # TODO: Let's implement client concept later
    sources = relationship("Source", back_populates="user")  # cascade="all, delete"
    conversations = relationship("Conversation", back_populates="user")  # cascade="all, delete"