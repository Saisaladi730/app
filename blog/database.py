from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import base64

# Database setup
DATABASE_URL = "sqlite:///./employees.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Employee(Base):
    __tablename__ = "employee_management"

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column("EmployeeName", String, index=True)  # Correct column name
    role = Column("Role", String)  # Correct column name
    email = Column("Email", String, unique=True)  # Correct column name
    phone = Column("Phone", String)  # Correct column name

class TimeLog(Base):
    __tablename__ = "time_logs"

    LogID = Column(Integer, primary_key=True, index=True)
    EmpID = Column(Integer, index=True)
    TimeIn = Column(DateTime, default=datetime.utcnow)
    TimeOut = Column(DateTime, nullable=True)
    Image = Column(Text, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)