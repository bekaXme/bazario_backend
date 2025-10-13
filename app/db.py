import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./bazario.db")
engine = create_engine(DATABASE_URL, echo=False)
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")

def get_session():
    with Session(engine) as session:
        yield session