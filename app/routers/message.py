from datetime import datetime, timezone
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, selectinload
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(prefix="/messages", 
                   tags=['Messages']) 

@router.get("/{chat_id}", response_model=List[schemas.MessageResponse])
def get_messages_by_chat(chat_id: int, db: Session = Depends(get_db)): 
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    messages = db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.created_at.asc()).all()
    return messages

@router.post("/{chat_id}", status_code = status.HTTP_201_CREATED, response_model=schemas.MessageResponse) 
def new_message(chat_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    msg = models.Message(chat_id=chat_id, content=message.content, role="user")
    
    chat.messages.append(msg)
    chat.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(msg)

    return msg
