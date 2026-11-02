# Healthcare Records Management (HCRM) System

A comprehensive healthcare records management system built with Django REST Framework (backend) and React (frontend), designed to manage patient records, appointments, and clinical workflows with enterprise-grade security.

## Overview

The HCRM System is a full-stack healthcare management platform that enables:
- **Patients** to register, manage profiles, book appointments, and view medical records
- **Clinicians** to manage daily schedules, create patient records, and add clinical notes
- **Administrators** to oversee users, generate reports, and manage system operations

## Key Features

### Patient Management (HCRM-F-001, F-002)
- Self-service patient registration with unique patient IDs
- Profile management (address, emergency contacts, allergies, blood group)
- Secure access to personal medical history

### Appointment System (HCRM-F-003 to F-007)
- Clinician search and availability checking
- Real-time appointment booking with conflict prevention
- Email reminders scheduled 24 hours before appointments when the Celery worker and broker are available
- Clinician daily dashboard with patient schedules

### Electronic Patient Records (HCRM-F-008 to F-010)
- Fernet-encrypted clinical record fields
- Clinical notes with audit trail
- Quick record creation workflow
- Secure patient history access

### Administrative Features (HCRM-F-011 to F-013)
- User management interface
- Clinician schedule management
- Patient volume reporting
- Appointment status tracking
- System audit logs

### Document Management (HCRM-F-014)
- Encrypted file upload/download
- Support for lab reports, imaging, prescriptions
- Secure document storage

## Architecture

### Backend (Django REST Framework)
```
hcrm-project/
├── authentication/          # User authentication & RBAC
├── patients/               # Patient profiles
├── appointments/           # Appointment booking & schedules
├── electronic_records/     # EPR with encryption
├── notifications/          # Email reminders (Celery)
├── audit_logs/            # Audit trail
├── reporting/             # Analytics & reports
└── hcrm_backend/          # Django settings & middleware
```

### Frontend (React + Material-UI)
```
frontend/
├── src/
│   ├── api/               # Axios API client
│   ├── components/        # Shared UI components
│   ├── modules/           # Feature modules
│   │   ├── auth/         # Login
│   │   ├── patient/      # Patient portal
│   │   ├── clinician/    # Clinician dashboard
│   │   └── admin/        # Admin panel
│   ├── store/            # Redux state management
│   └── utils/            # Helper functions
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis (for Celery)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd hcrm-project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create `.env` file in project root:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=hcrm_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Encryption (Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
HCRM_ENCRYPTION_KEY=your-fernet-encryption-key

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@hcrm.local
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start development server**
```bash
python manage.py runserver
```

Backend API will be available at `http://localhost:8000`

After pulling updates, back up the database and run `python manage.py migrate` before starting the application. Existing patient and appointment IDs remain unchanged; newly generated IDs use a longer `PAT` or `APT` identifier. Registration now requires `user.password_confirm` in addition to `user.password`.

For email reminders, configure `CELERY_BROKER_URL`, SMTP settings, and run `celery -A hcrm_backend worker --loglevel=info` alongside the application. Reminder dispatch currently logs broker failures; it does not guarantee delivery or retry failed scheduling. SMS is not available.

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment**
Create `.env` file in `frontend/`:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

4. **Start development server**
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Security Features

### Authentication & Authorization (HCRM-SR-002, SR-003)
- JWT-based authentication with refresh tokens
- Role-Based Access Control (RBAC): Patient, Clinician, Admin
- Token expiration: 24 hours (access), 7 days (refresh)
- MFA enrollment and verification are not implemented. Accounts marked `mfa_enabled` cannot log in until that workflow is available.

### Data Encryption (HCRM-SR-001)
- Fernet symmetric encryption for selected clinical record fields and documents
- Encrypted file storage for documents
- HTTPS is required for production; configure TLS at the deployment proxy

### Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security

### Audit Logging (HCRM-SR-004)
- Database-backed audit events for implemented actions, including record history reads
- Audit entries include user, action, timestamp, and an optional IP address
- Database-level immutability and a retention policy are not yet implemented

## API Documentation

### Authentication Endpoints
```
POST   /api/v1/auth/login/              # Login (get JWT tokens)
POST   /api/v1/auth/token/refresh/      # Refresh access token
```

### Patient Endpoints
```
POST   /api/v1/patients/register/       # Register new patient
GET    /api/v1/patients/profile/        # Get patient profile
PATCH  /api/v1/patients/profile/        # Update patient profile
```

### Appointment Endpoints
```
GET    /api/v1/appointments/            # List user's appointments
POST   /api/v1/appointments/book/       # Book appointment
GET    /api/v1/appointments/search/     # Search clinicians
GET    /api/v1/appointments/availability/:id/  # Check availability
GET    /api/v1/appointments/dashboard/  # Clinician daily schedule
PATCH  /api/v1/appointments/status/:id/ # Update appointment status
```

### Electronic Records Endpoints
```
GET    /api/v1/records/:patient_id/history/  # Patient medical history
POST   /api/v1/records/quick-create/          # Create patient record
POST   /api/v1/records/notes/add/             # Add clinical note
POST   /api/v1/records/documents/upload/      # Upload document
GET    /api/v1/records/documents/             # List documents
```

### Admin Endpoints
```
GET    /api/v1/admin/users/            # List all users
GET    /api/v1/admin/logs/             # View audit logs
POST   /api/v1/reports/patient-volume/ # Generate report
POST   /api/v1/appointments/schedule/  # Manage clinician schedules
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Suites
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# System tests
pytest tests/system/

# Performance tests
pytest tests/performance/
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
```

### Performance Testing
```bash
# Database performance (must complete in ≤7 seconds)
pytest tests/performance/test_database_performance.py

# Load testing with Locust (500 concurrent users)
cd tests/performance
locust -f locustfile.py --host=http://localhost:8000
```

## Performance Requirements

- **Transaction Time** (HCRM-NF-001): Appointment booking ≤ 10 seconds
- **Load Time** (HCRM-NF-002): Record creation/view ≤ 5 seconds
- **Concurrent Users** (HCRM-NF-003): Support 500+ concurrent users
- **Database Performance** (HCRM-NF-004): Search with 10K+ records ≤ 7 seconds

## CI/CD Pipeline

The project includes GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. **Build & Test**
   - Sets up Python 3.11 and Node.js 18
   - Installs backend/frontend dependencies
   - Runs Django migrations
   - Executes pytest test suite
   - Runs performance benchmarks
   - Builds React frontend

2. **Deployment**
   - No deployment target is configured. The preparation script fails explicitly after its checks until a target is provided.

### Running CI/CD Locally
```bash
# Backend tests
python manage.py migrate
pytest --disable-warnings

# Performance tests
pytest tests/performance/test_database_performance.py --benchmark-only

# Frontend build
cd frontend
npm ci
npm run build
```

## Deployment

### Production Checklist

1. **Environment Configuration**
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=<strong-random-secret>
HCRM_ENCRYPTION_KEY=<production-fernet-key>

# Use production database
DB_HOST=production-db-host
DB_PASSWORD=<secure-password>

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

2. **Security Settings**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

3. **Static Files**
```bash
python manage.py collectstatic --noinput
```

4. **Database Migrations**
```bash
python manage.py migrate --noinput
```

5. **Application Server**
   - Use Gunicorn/uWSGI for Django
   - Use Nginx as reverse proxy
   - Enable HTTPS with SSL certificates

## Project Structure Highlights

### Backend Services
- **Authentication**: Custom User model with RBAC
- **Appointments**: Schedule management, booking, conflict detection
- **Electronic Records**: Encrypted PHI storage with Fernet
- **Notifications**: Celery tasks for email reminders; SMS is not implemented
- **Audit Logs**: Database-backed events; immutable retention is not implemented

### Frontend Modules
- **Auth**: Login with JWT token management
- **Patient Portal**: Dashboard, appointments, medical records
- **Clinician Dashboard**: Daily schedule, patient notes, record creation
- **Admin Panel**: User management, reporting, system logs

---
