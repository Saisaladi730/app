from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel
from blog.database import SessionLocal, Employee, EmployeeAttendance
from fastapi.staticfiles import StaticFiles
from typing import Dict
import sqlite3
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from typing import Optional

app =FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

# Pydantic models for validation
class EmployeeBase(BaseModel):
    id : int
    name: str
    email: str
    phone: str
    status: str

class EmployeeBase1(BaseModel):
    name: str
    email: str
    phone: str
    status: str

class TimeInRequest(BaseModel):
    EmpID: int
    Image: str  # Base64 encoded image data
    timein : str
    employeename : str

class TimeOutRequest(BaseModel):
    EmpID: int
    timeout : str
    image : str


# Pydantic Model for Report
class TimeLogReport(BaseModel):
    time_in: datetime
    time_out: datetime
    hours_spent: float

class EmployeeTimeInTimeOut(BaseModel):
    timein : Optional[str]
    timeout : Optional[str]


# Routes
@app.post("/login")
async def login(login_request: LoginRequest):
    username = login_request.username
    password = login_request.password

    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM admin WHERE username = ? AND password = ?", (username, password)
    )
    admin = cursor.fetchone()
    conn.close()

    if admin:
        return "Login successfull"
    else:
        # raise HTTPException(status_code=401, detail="Invalid username or password")
        return "Login unsuccessfull"


@app.post("/EmployeeManagement")
def add_employee(employee: EmployeeBase1, db: Session = Depends(get_db)):
    new_employee = Employee(
        name=employee.name,
        email=employee.email,
        phone=employee.phone,
        status=employee.status,
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

@app.get("/getEmployees", response_model=List[EmployeeBase])
def get_all_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees

@app.put("/update-employees")
def update_employees(employee: EmployeeBase, db: Session = Depends(get_db)):
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    try:
        # Update employee details in the database
        cursor.execute(
            """
            UPDATE employees 
            SET name = ?, email = ?, phone = ?, status = ? 
            WHERE id = ?
            """,
            (employee.name, employee.email, employee.phone, employee.status, employee.id),
        )
        conn.commit()  # Save changes to the database
        return {"message": "Employee updated successfully."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


@app.post("/employees/time-in")
def time_in_employee( time_in_data: TimeInRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == time_in_data.EmpID).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    time_log = EmployeeAttendance(
        EmpId=time_in_data.EmpID,
        PhotoTimeIn=time_in_data.Image,
        TimeIn = time_in_data.timein,
        EmployeeName = time_in_data.employeename
    )
    db.add(time_log)
    db.commit()
    db.refresh(time_log)
    return {"message": "Time-in recorded", "log_id": time_log.EmpId}

@app.post("/employees/time-out")
def time_out_employee(time_out_data: TimeOutRequest, db: Session = Depends(get_db)):
    # Find the last time-in record without a time-out
    time_log = db.query(EmployeeAttendance).filter(EmployeeAttendance.EmpId == time_out_data.EmpID, EmployeeAttendance.TimeOut == None).first()
    if not time_log:
        raise HTTPException(status_code=404, detail="No active time-in record found")
    
    # Set the time-out
    time_log.TimeOut = time_out_data.timeout
    time_log.PhotoTimeOut = time_out_data.image
    db.commit()
    return {"message": "Time-out recorded", "log_id": time_log.EmpId}

@app.get("/GetEmployeesTimeInTimeOut")
def time_out_employee(db: Session = Depends(get_db)):
    employees = db.query(EmployeeAttendance).all()
    return employees






    
