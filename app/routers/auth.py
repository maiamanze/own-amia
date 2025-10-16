from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2

router = APIRouter(tags=['Authentication'])

@router.post("/login", response_model=schemas.Token)
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)): # espera las credenciales en form-data, no raw
    user = db.query(models.User).filter(models.User.email == credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    
    if not utils.verify(credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    
    token = oauth2.create_token(data = {"user_id": user.id}) # a elección y opcional; qué enviar en el payload
    return {"token": token, "type": "bearer"}