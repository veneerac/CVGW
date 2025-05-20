
# Job Portal API

A RESTful API for a job portal system built with Flask and SQLAlchemy, featuring user roles, job management, and application tracking with XML responses.

## Features

- User roles: Admin, Recruiter, User
- User registration & profile management
- Job posting & management
- Job application system
- Approval workflows for users/jobs
- XML-based API responses
- SQLite database (default)
- Email validation


## Technologies Used

- Python 3.9+
- Flask
- SQLAlchemy
- XML processing
- email-validator

## Installation

### Prerequisites
- Python 3.9+ installed
- pip package manager
- Git (optional)

### Steps

1. **Clone repository**
   ```bash
   git clone[ https://github.com/yourusername/job-portal-api.git](https://github.com/veneerac/CVGW
   cd CVGW
   ```

2. **Install dependencies**
   ```bash
   pip3 install flask_sqlalchemy
   pip3 install email_validator
   ```

   Required packages (if not using requirements.txt):
   ```bash
   pip install Flask Flask-SQLAlchemy email-validator requests lxml
   ```

3. **Configure environment**
   ```bash
   # Linux/macOS
   export FLASK_APP=app.py
   export FLASK_ENV=development

   # Windows
   set FLASK_APP=app.py
   set FLASK_ENV=development
   ```

```

## API Documentation

### Key Endpoints

| Method | Endpoint                | Description                          |
|--------|-------------------------|--------------------------------------|
| POST   | /users                  | Create new user                      |
| PUT    | /users/{id}/approve     | Approve user (Admin)                 |
| POST   | /jobs                   | Create job post (Recruiter)          |
| PUT    | /jobs/{id}/approve      | Approve job post (Admin)             |
| POST   | /jobs/{id}/apply        | Apply for job (User)                 |
| GET    | /applications           | View applications (User/Recruiter)   |

Download CV_gateway.postman_collection.json collection 

### User Information

| Username                 | Password     | Role      |
|--------------------------|--------------|-----------|
| admin@example.com        | adminpass    | ADMIN     |
| recruiter@example.com    | secret123    | RECRUITER |
| hr.sarah@careers.org     | HrMaster$55  | USER      |



### Example Requests

**Create User:**
```bash
curl -X POST http://localhost:5000/users \
  -d "email=user@example.com" \
  -d "password=secret123" \
  -d "first_name=John" \
  -d "last_name=Doe" \
  -d "date_of_birth=1990-01-01" \
  -d "address=123 Main St"
```

**Approve User (Admin):**
```bash
curl -X PUT http://localhost:5000/users/2/approve \
  -d "admin_email=admin@example.com"
```

**Create Job (Recruiter):**
```bash
curl -X POST http://localhost:5000/jobs \
  -d "email=recruiter@company.com" \
  -d "password=recruiterpass" \
  -d "title=Software Engineer" \
  -d "company=Tech Corp" \
  -d "description=Develop amazing software" \
  -d "required_skills=Python,Flask" \
  -d "posting_date=2023-08-01"
```
 Note: Use the default database in the report unless a change is explicitly requested. To switch the database, use the following commands:


**Reset Database:**
```bash
rm instance/app.db
```

## Project Structure

```
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── instance/
│   └── app.db            # Database file
├── README.md              # This document
└── tests/                 # Test scripts
```


## Acknowledgments

- Flask development team
- SQLAlchemy ORM
- email-validator library
```

