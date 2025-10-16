from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # determino el algoritmo de hashing

def hash(password: str):
    print("Hashing password:", password)  
    return pwd_context.hash(password)

def verify(plain, hashed):
    return pwd_context.verify(plain, hashed)