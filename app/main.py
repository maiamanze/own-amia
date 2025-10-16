from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # For CORS blocking solution
from . import models
from .database import engine
from .routers import user, chat, auth, message

models.Base.metadata.create_all(bind=engine)

app = FastAPI() 

app.include_router(user.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(message.router)
