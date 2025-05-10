from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import StreamingResponse # type: ignore

import uvicorn # type: ignore

from pydantic import BaseModel # type: ignore
from typing import AsyncGenerator

from sqlalchemy import Column, Integer, String, Boolean # type: ignore    # type: ignore
from sqlalchemy.orm import Session           # type: ignore

import os
import re
import json
import asyncio

from langchain_google_genai import GoogleGenerativeAIEmbeddings # type: ignore 

import utils.auth as auth
import utils.emailer as emailer
from utils.db_client import ConnectPostgres
from utils.validators import validate_captcha
from utils.errors import RateLimitError
from ai import get_graph



### Serving model outputs via FastAPI
### Copyright (c) Jani Kuhno


# Pydantic requests and responses

# For generation
class TextRequest(BaseModel):
    input: str
    location: dict

# For authentication

class User(auth.Base):
    __tablename__ = "users_table"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ContactForm(BaseModel):
    email: str
    contact: str
    captcha: str

class UserResendVerification(BaseModel):
    email: str


# FastAPI app
app = FastAPI()

# Add a router
api_router = APIRouter(prefix='/api')

# Avoid CORS issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# langgraph CompiledGraph
graph = None

# CryptContext for password hashing
pwd_context = auth.get_crypt_context()

DOMAIN = os.getenv("DOMAIN")



@app.on_event("startup")
async def load_models():
    global graph

    # Load embeddings
    EMBED_MODEL_NAME = "models/text-embedding-004"

    # This is from google's docs. If unsure, use len(embeddings.embed_query("hello world"))
    DIMS = 768
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL_NAME)

    # Postgres
    db = ConnectPostgres(embeddings, DIMS)

    with db.get_store() as store:
        store.setup()

    graph = get_graph(db)
    print("\nLoaded embedding model, FAISS and Postgres stores.\n")


@api_router.post("/generate")
async def generate_answer(user_input: TextRequest, 
                          user_email: str = Depends(auth.get_current_user),
                          user_db: Session = Depends(auth.get_db)):
    
    input = user_input.input
    
    user = user_db.query(User).filter(User.email == user_email).first()


    config = {"configurable": {
                              
                              "user_id": str(user.id),
                              "location": user_input.location,
                              }
    } 

   
    # Create async generator for streaming custom updates from nodes
    async def event_stream() -> AsyncGenerator[str, None]:
        chunks = []
        try:
            async for metadata, chunk in graph.astream(input={"input": input}, config=config, stream_mode=['values', 'custom']):
                if metadata == 'values':
                    chunks.append(chunk)
                if metadata == 'custom':
                    update = {
                        "status": "processing",
                        "output": chunk["custom_key"]
            
                    }
                    
                    await asyncio.sleep(0.5)  # Small delay to prevent flooding
                    
                    yield f"data: {json.dumps(update)}\n\n"
                    
        # raise RateLimitError('Rate limits hit', 'Google Maps API')
        except RateLimitError as e:
            update = {
                        "status": 429,
                        "output": str(e)
            
                    }
            yield f"data: {json.dumps(update)}\n\n"     


        # Final output
    
        if "output" in chunks[-1].keys():
            # List of Documents
            output_list = chunks[-1]["output"]
    
            result = {}
            final_update = {
                "status": "complete",
                "output": result
            }

            
            for i, output in enumerate(output_list):
                output_data = {}
                # (name, score, rating, delivery, maps_uri, photo)
                output_data["name"] = output[0]
                output_data["rating"] = output[2]
                output_data["delivery"] = output[3]
                output_data["maps_uri"] = output[4]
                output_data["photo"] = output[5]
                final_update["output"][str(i)] = output_data
    
    
        elif "decision" in chunks[-1].keys():
            if "end" in chunks[-1]["decision"]:
                final_update = {
                        "status": "end",
                        "output": 'Saved a liking'
                    }
        else:
            final_update = {
                    "status": 'end',
                    "output": "Should probably raise an error"
                }
    
        yield f"data: {json.dumps(final_update)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@api_router.post("/register")
def register(user: UserCreate, background_tasks: BackgroundTasks, user_db: Session = Depends(auth.get_db)):
    # Validate email format
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user.email)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid email")
    
    # Validate pw length
    if len(user.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    
    # Check if user already exists
    db_user = user_db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    

    # Hash password and save user to database
    hashed_password = pwd_context.hash(user.password)

    
    verification_token = auth.create_access_token({"sub": user.email})

    db_user = User(email=user.email, password=hashed_password, is_verified=False, verification_token=verification_token)
    user_db.add(db_user)
    user_db.commit()

    # Notify me of new users
    background_tasks.add_task(emailer.send_email, 
                              "info@wtf2eat.com", 
                              "New user registered", 
                              user.email, 
                            )

    verification_link = f"{DOMAIN}/verify-email?token={verification_token}"
    email_body = f"""Click the link to verify your email: 
    
    {verification_link}"""
    background_tasks.add_task(emailer.send_email, 
                              user.email, 
                              "Verify Your Email", 
                              email_body, 
                              )

    return {"message": "User registered. Check your email to verify your account."}


@api_router.get("/verify-email")
def verify_email(token: str, user_db: Session = Depends(auth.get_db)):
    
    # Check the token is valid and not expired
    try:
        user_email = auth.get_current_user(token)
    except HTTPException as e:
        print(f'User: {user_email}, Status: {e}')
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")


    # Check the link matches with the latest token
    db_user = user_db.query(User).filter(User.verification_token == token).first()

    if not db_user or db_user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid or already verified token. Use the latest link.")
    
    # Mark user as verified
    db_user.is_verified = True
    db_user.verification_token = None  # Remove token
    user_db.commit()

    return {"message": "Email successfully verified"}


@api_router.post("/resend-verification")
def resend_verification(user: UserResendVerification, background_tasks: BackgroundTasks, user_db: Session = Depends(auth.get_db)):
    email = user.email
    
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid email")
    
    db_user = user_db.query(User).filter(User.email == email).first()

    if not db_user or db_user.is_verified:
        raise HTTPException(status_code=400, detail="User not found or already verified")

    # Generate new token
    verification_token = auth.create_access_token({"sub": db_user.email})
    db_user.verification_token = verification_token
    user_db.commit()

    # Send new verification email
    verification_link = f"{DOMAIN}/verify-email?token={verification_token}"
    email_body = f"""Click the link to verify your email: 
    
    {verification_link}"""
    background_tasks.add_task(emailer.send_email, 
                              db_user.email, 
                              "Verify Your Email", 
                              email_body, 
                              )

    return {"message": "Verification email resent"}


@api_router.post("/login")
def login(user: UserLogin, user_db: Session = Depends(auth.get_db)):
    # Validate email
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user.email)
    if valid:
        db_user = user_db.query(User).filter(User.email == user.email).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid email")
    
    # Check if user exists and password is correct
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not db_user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified. Please check your inbox.")

    token = auth.create_access_token({"sub": user.email})

    # Return JWT token
    return {"access_token": token, "token_type": "bearer"}


@api_router.post("/contact")
async def contact(user: ContactForm):
    # Validate CAPTCHA
    if not validate_captcha(user.captcha):
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA")

    # Validate email
    valid_email = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user.email)
    valid_msg = len(user.contact) > 0
    if not valid_email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not valid_msg:
        raise HTTPException(status_code=400, detail="Message must not be empty")
    else:
        try:
            await emailer.send_email("info@wtf2eat.com", user.email, user.contact)
            return {"message": "Email sent successfully"}
        except HTTPException as e:
            print(e)
            raise HTTPException(status_code=500, detail="Email sending failed")
    
# Server init

app.include_router(api_router)

auth.Base.metadata.create_all(bind=auth.engine)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)