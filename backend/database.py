from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker







Base = declarative_base()

class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    role = Column(String)

    