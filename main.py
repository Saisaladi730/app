from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel
from blog.database import SessionLocal, Employee, TimeLog
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

class EmployeeCreate(BaseModel):
    employee_name: str
    role: str
    email: str
    phone: str
    status: str

class TimeInRequest(BaseModel):
    EmpID: int
    Image: str  # Base64 encoded image data

class TimeOutRequest(BaseModel):
    EmpID: int


# @app.post("/login")
# async def login(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# Create the route for handling login via POST
# @app.post("/login")
# async def login_post(login_request: LoginRequest):
#     # Validate username and password (simple check)
#     if login_request.username == "admin@example.com" and login_request.password == "admin123":
#         return {"success": True}  # Successful login response
#     else:
#         raise HTTPException(status_code=401, detail="Invalid username or password")

#@app.get("/add-employee-management")
#async def add_employee_management(request: Request):
    #return templates.TemplateResponse("add-employee-management.html", {"request": request})



#@app.post("/add-employee")
#async def add_employee(employee: Employee):
    #employees.append(employee.dict())
    #return {"message": "Employee added successfully", "data": employee}



#@app.post("/api/employees")
#async def create_employee(employee: EmployeeCreate, db: SessionLocal = Depends(get_db)):
    #db_employee = Employee(name=employee.name, email=employee.email, phone=employee.phone, status=employee.status)
    #db.add(db_employee)
    #db.commit()
    #db.refresh(db_employee)
    #return db_employee

#@app.get("/api/employees")
#async def get_employees(db: SessionLocal = Depends(get_db)):
    #employees = db.query(Employee).all()
    #return employees



#@app.get("/", response_class=HTMLResponse)
#async def register(request: Request):
    #return templates.TemplateResponse("register.html", {"request": request})


# Add Employee Management route
#@app.get("/add-employee-management", response_class=HTMLResponse)
#async def add_employee_management(request: Request):
    #return templates.TemplateResponse("add-employee-management.html", {"request": request})


#@app.get("/monthly-report")
#async def monthly_report(request: Request):
    #return templates.TemplateResponse("monthly-report.html", {"request": request})



# Route for the Employee Monthly Reports page
#@app.get("/employee-reports", response_class=HTMLResponse)
#async def employee_reports(request: Request):
    # You can pass dynamic data to the template (e.g., employees, months)
    #return templates.TemplateResponse("employee-reports.html", {"request": request})

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


@app.post("/employees/")
def add_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    # Check if employee already exists (based on email)
    db_employee = db.query(Employee).filter(Employee.email == employee.email).first()
    if db_employee:
        raise HTTPException(status_code=400, detail="Employee with this email already exists.")
    
    # Create new employee instance
    new_employee = Employee(
        employee_name=employee.employee_name,
        role=employee.role,
        email=employee.email,
        phone=employee.phone,
        status=employee.status
    )

    # Add the employee to the database
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee

@app.get("/employees/", response_model=List[EmployeeCreate])
def get_all_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees

@app.post("/employees/{emp_id}/time-in")
def time_in_employee(emp_id: int, time_in_data: TimeInRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.EmpID == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    time_log = TimeLog(
        EmpID=emp_id,
        Image=time_in_data.Image,
    )
    db.add(time_log)
    db.commit()
    db.refresh(time_log)
    return {"message": "Time-in recorded", "log_id": time_log.LogID}

@app.post("/employees/{emp_id}/time-out")
def time_out_employee(emp_id: int, time_out_data: TimeOutRequest, db: Session = Depends(get_db)):
    # Find the last time-in record without a time-out
    time_log = db.query(TimeLog).filter(TimeLog.EmpID == emp_id, TimeLog.TimeOut == None).first()
    if not time_log:
        raise HTTPException(status_code=404, detail="No active time-in record found")
    
    # Set the time-out
    time_log.TimeOut = datetime.utcnow()
    db.commit()
    return {"message": "Time-out recorded", "log_id": time_log.LogID}


# Pydantic Model for Report
class TimeLogReport(BaseModel):
    time_in: datetime
    time_out: datetime
    hours_spent: float

# Generate Monthly Report
@app.get("/employees", response_model=List[TimeLogReport])
def generate_report(emp_id: int, month: int, year: int, db: SessionLocal = Depends(get_db)):
    logs = (
        db.query(TimeLog)
        .filter(
            TimeLog.emp_id == emp_id,
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
