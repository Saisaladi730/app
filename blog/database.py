from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import base64

DATABASE_URL = "sqlite:///./employees.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class Login(Base):
    __tablename__ = "admin"
    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String,  nullable=False)
    status = Column(String, nullable=False)


class EmployeeAttendance(Base):
    __tablename__ = "EmployeeAttendance"

    id = Column(Integer, primary_key=True, index=True)
    EmpId = Column(Integer, index=True)
    EmployeeName = Column(String, index=True)
    TimeIn = Column(DateTime, default=datetime.now())
    TimeOut = Column(DateTime, nullable=True)
    PhotoTimeIn = Column(Text, nullable=True)
    PhotoTimeOut = Column(Text, nullable=True)

Base.metadata.create_all(bind=engine)