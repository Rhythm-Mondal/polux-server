import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

db_url = "postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}".format(
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PWD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
