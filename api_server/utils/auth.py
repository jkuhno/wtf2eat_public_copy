from sqlalchemy import create_engine # type: ignore
from sqlalchemy.ext.declarative import declarative_base     # type: ignore
from sqlalchemy.orm import sessionmaker          # type: ignore
from fastapi.security import OAuth2PasswordBearer # type: ignore
from fastapi import HTTPException, Security # type: ignore

from passlib.context import CryptContext # type: ignore
import jwt # type: ignore

from cryptography.fernet import Fernet # type: ignore

from datetime import datetime, timedelta
import os


SECRET_KEY = os.environ['JWT_SECRET_KEY']
ALGORITHM = "HS256"

FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY.encode())

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

user = os.environ['POSTGRES_USER']
pw = os.environ['POSTGRES_PASSWORD']
host = os.environ['POSTGRES_HOST']

DATABASE_URL = f"postgresql://{user}:{pw}@{host}:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_crypt_context():
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")  # `sub` should contain the user's ID in the token

        if not user_email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        return user_email  # Return the user ID
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")
    
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid authentication token: 'not enough segments'")

    # Not raising errors here, maybe if these fail often something like 'something went wrong''


def encrypt(api_key: str) -> str:
    """Encrypts an API key for secure storage."""
    return fernet.encrypt(api_key.encode()).decode()

def decrypt(encrypted_key: str) -> str:
    """Decrypts an API key for internal use."""
    return fernet.decrypt(encrypted_key.encode()).decode()