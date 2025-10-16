from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime 

# Token
class Token(BaseModel):
    token: str
    type: str 

class TokenData(BaseModel):
    id: Optional[int] = None
    

# User
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str 

class UserResponse(UserBase): # NO devuelve password!
    id: int 
    created_at: datetime

    model_config = {"from_attributes": True}


# Chat
class ChatBase(BaseModel):
    title: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    user: UserResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Message
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    chat: ChatResponse 
    content: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
