from datetime import datetime, timezone
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, selectinload
from .. import models, schemas, oauth2
from ..database import get_db
from .message import new_message
from ollama import chat, ChatResponse

router = APIRouter(prefix="/chats", 
                   tags=['Chats']) 

@router.get("/", response_model=List[schemas.ChatResponse])
def get_all_by_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return db.query(models.Chat).filter(models.Chat.user_id == current_user.id).all()

@router.get("/{id}", response_model=schemas.ChatResponse)
def get_by_user(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):       
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

@router.put("/{id}", response_model=schemas.ChatResponse) 
def update_chat(id: int, updated_chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    find_chat = db.query(models.Chat).filter(models.Chat.id == id)
    chat = find_chat.first()
    if not chat:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Chat with id {id} does not exist")

    find_chat.update(updated_chat.model_dump(), synchronize_session=False)
    db.commit()

    return find_chat.first() 

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

@router.post("/talk/{id}", response_model=schemas.MessageResponse)
def send_message(id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    chat_db = db.query(models.Chat).options(selectinload(models.Chat.messages)).filter(models.Chat.id == id, models.Chat.user_id == current_user.id).first()
    if not chat_db: # Creo uno nuevo 
        chat_db = models.Chat(user_id=current_user.id, title="New chat", created_chat=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db.add(chat_db)
        db.commit()
        db.refresh(chat_db)

    # Guardo el msj del usuario
    user_msg = models.Message(chat_id=chat_db.id, role="user", content=message.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Construyo el contexto con los mensajes previos de ese chat
    context = []
    if len(chat_db.messages) == 0:
        context.append({
            "role": "system", # comportamiento
            "content": "Eres un asistente útil, conciso y preciso. Responde de manera directa sin inventar contexto innecesario."
        })

    context += [
        {"role": msg.role, "content": msg.content}
        for msg in chat_db.messages[-10:] # solo los últimos 10 para no sobrecargar tanto
    ] 
    context.append({"role": "user", "content": message.content}) # agrego el nuevo mensaje

    response: ChatResponse = chat(model="llama2", messages=context)
    clean_response = response.message.content.strip() # quita /n (menos el del principio), espacios...

    # Guardo la rta del modelo
    model_msg = models.Message(chat_id=chat_db.id, role="assistant", content=clean_response)
    db.add(model_msg)
    db.commit()
    db.refresh(model_msg)

    return model_msg

    
        
