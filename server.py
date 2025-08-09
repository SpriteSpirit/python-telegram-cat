from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import datetime
from random import randint

app = Flask(__name__)
engine = create_engine("sqlite:///database.db")
Base = declarative_base()


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    x = Column(Integer)
    y = Column(Integer)
    coins = Column(Integer)
    joined_at = Column(DateTime)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
