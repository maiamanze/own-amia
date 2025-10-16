from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_token(data: dict):
    copy = data.copy() # payload to encode into our token
    expire = datetime.now() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    copy.update({"expiration": expire.isoformat()})

    token = jwt.encode(copy, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")) 

    return token

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        id: str = payload.get("user_id")

        if not id:
            raise credentials_exception
        
        token_data = schemas.TokenData(id=id)
    except JWTError: 
        raise credentials_exception
    
    return token_data
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    token = verify_token(token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == token.id).first()
    return user