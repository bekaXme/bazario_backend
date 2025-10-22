import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

load_dotenv()

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./bazario.db")
engine = create_engine(DATABASE_URL, echo=False)

# Upload directory for images
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure folder exists

# FastAPI app (used for mounting static files)
app = FastAPI(title="Bazario API")

# Serve uploads folder as static files so Flutter can access them
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Database session generator
def get_session():
    with Session(engine) as session:
        yield session
