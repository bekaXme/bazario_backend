from sqlmodel import create_engine, Session
import os
from dotenv import load_dotenv
load_dotenv()
from os import environ


DATABASE_URL = environ.get("DATABASE_URL", "sqlite:///./bazario.db")
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    from app import models
    models.SQLModel.metadata.create_all(engine)