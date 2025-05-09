
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
- Admin dashboard capabilities

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
   git clone https://github.com/yourusername/job-portal-api.git
   cd job-portal-api
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

4. **Initialize database**
   ```bash
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

## Running the Server

```bash
CVgateway/python3 app.py
```

The API will be available at `http://localhost:5000`

## Configuration

Create `.env` file for environment variables:
```env
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=adminpass
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

## Database Management

**Initialize Database:**
```python
from app import db
db.create_all()
```

**Reset Database:**
```bash
rm instance/app.db
```

Or manually test with cURL/Postman using the examples provided above.

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

