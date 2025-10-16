from datetime import datetime, timezone
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, selectinload
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(prefix="/chats", 
                   tags=['Chats']) 

# TODO update (title and updated_at)

@router.get("/", response_model=List[schemas.ChatResponse])
def get_by_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return db.query(models.Chat).filter(models.Chat.user_id == current_user.id).all()

@router.get("/{id}", response_model=schemas.ChatResponse)
def get_chat(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    chat = db.query(models.Chat).filter(models.Chat.id == id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    return chat

@router.post("/", status_code = status.HTTP_201_CREATED, response_model=schemas.ChatResponse) 
def new_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    new_chat = models.Chat(**chat.model_dump(), user_id = current_user.id) 
    db.add(new_chat)
    db.commit() 
    db.refresh(new_chat) 

    return new_chat 

@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_chat(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    find_chat = db.query(models.Chat).filter(models.Chat.id == id, models.Chat.user_id == current_user.id)
    if not find_chat.first():
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Chat with id {id} does not exist or does not belong to the current user")
    
    find_chat.delete(synchronize_session=False) # opción más eficiente
    db.commit()

    return Response(status_code = status.HTTP_204_NO_CONTENT)

@router.delete("/clear/{id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_chat(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    chat = db.query(models.Chat).filter(models.Chat.id == id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat does not exist or does not belong to the current user")

    deleted = (db.query(models.Message).filter(models.Message.chat_id == id).delete(synchronize_session=False))

    chat.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"deleted": deleted}