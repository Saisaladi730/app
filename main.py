from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel
from blog.database import SessionLocal, Employee, TimeLog ,EmployeeAttendance
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

# Login Database Setup
def init_db():
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO admins (username, password)
        VALUES ('admin', 'password123')
        """
    )
    conn.commit()
    conn.close()

init_db()

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

    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM admins WHERE username = ? AND password = ?", (username, password)
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

@app.post("/employees/time-in")
def time_in_employee( time_in_data: TimeInRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == time_in_data.EmpID).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Store the time-in record with the photo (base64 image)
    # time_log = TimeLog(
    #     EmpID=emp_id,
    #     Image=time_in_data.Image,s
    # )
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
    # conn = sqlite3.connect("employees.db")
    # cursor = conn.cursor()

    # # Fetch all rows
    # cursor.execute("SELECT id, employee_id, timein, timeout FROM EmployeeAttendance")
    # rows = cursor.fetchall()

    # # Convert rows into a list of dictionaries
    # result = []
    # for row in rows:
    #     result.append({
    #         "id": row[0],
    #         "employee_id": row[1],
    #         "timein": row[2] if row[2] else None,  # Convert datetime to ISO string
    #         "timeout": row[3] if row[3] else None,
    #         # "photo": row[4].hex() if row[4] else None,  # Convert BLOB to hex string (or handle as needed)
    #     })
    # conn.close()
    # return result

# Generate Monthly Report
@app.get("/employees", response_model=List[TimeLogReport])
def generate_report(employee_name: str, month: int, year: int, db: SessionLocal = Depends(get_db)):
    logs = (
        db.query(TimeLog)
        .filter(
            TimeLog.employee_name == employee_name,
            TimeLog.time_in != None,
            TimeLog.time_out != None,
            TimeLog.time_in.between(
                datetime(year, month, 1),
                datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1),
            ),
        )
        .all()
    )
    report = [
        TimeLogReport(
            time_in=log.time_in,
            time_out=log.time_out,
            hours_spent=(log.time_out - log.time_in).total_seconds() / 3600,
        )
        for log in logs
    ]
    return report
