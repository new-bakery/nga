# Backend Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory with the following content:
```
# Database settings
DATABASE_URL=sqlite:///./sql_app.db

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Aliyun OSS Settings (required for file uploads)
OSS_ACCESS_KEY_ID=your-access-key-id
OSS_ACCESS_KEY_SECRET=your-access-key-secret
OSS_BUCKET_NAME=your-bucket-name
OSS_ENDPOINT=your-oss-endpoint
```

Note: Make sure to change `your-secret-key-here` and the OSS credentials to your actual values in production.

## Database Initialization

1. Initialize the database and create an admin user:
```bash
python init_db.py
```

This will:
- Create all necessary database tables
- Create an admin user with the following credentials:
  - Username: admin
  - Password: admin123 (change this in production)
- Add some sample system data sources

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`



# Alembic Command Line Reference:

- alembic revision --autogenerate -m "Initial migration"
- alembic upgrade head
