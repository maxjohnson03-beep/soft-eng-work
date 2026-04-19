# database.py — sets up the SQLite database and defines the User table
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker




# Base class that all database models inherit from
Base = declarative_base()

# User table — stores registered users, their hashed passwords and roles
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    role = Column(String)

# Connect to the SQLite database file (created automatically if it doesn't exist)
engine = create_engine("sqlite:///./gcs.db")

# SessionLocal is used to create database sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the database if they don't already exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
