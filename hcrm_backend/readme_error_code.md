Healthcare Appointment & Patient Record Manager

(PESU_RR_CSE_A_P22_Healthcare_Appointment_and_Patient_Record_Manager_Oura-Oura)

A secure, full-stack healthcare appointment and electronic health record (EHR) management system built using:

Django 4.2

Django REST Framework (DRF)

PostgreSQL

JWT Authentication

Fernet-encrypted file storage

React (external frontend)

This backend delivers robust services for authentication, appointments, patient records, audit trails, encryption, and reporting.

🚀 Features
✔ Core Functionalities

User registration, login, JWT refresh & rotation

Patient profile + demographic management

Appointment scheduling & lifecycle management

Secure electronic health record upload & retrieval

Fernet-encrypted medical file storage (PDFs, diagnostic reports, etc.)

Notification service

Audit logging (request history, admin tracking)

Reporting endpoints for analytics

🔐 Sprint 2 Enhancements (Security + Error Handling)
Fail-fast Fernet Key Validation

Startup now stops immediately if:

Encryption key is missing

Invalid key format

Wrong key regeneration attempt

Prevents silent decryption failures and inconsistent data encryption.

Location:
hcrm_backend/__init__.py

Unified Encryption Module

All encryption logic is consolidated into a single Fernet manager.

Canonical key: HCRM_ENCRYPTION_KEY

Backwards compatibility: MY_FERNET_KEY supported

Consistent API:

encrypt(plaintext)
decrypt(token)

encrypt_file(byte_data)
decrypt_file(byte_data)


Location:
electronic_records/encryption.py

Improved Global Exception Handling

A custom DRF exception handler:

Sanitizes sensitive error messages

Ensures consistent response format

Prevents leakage of stack traces

Location:
hcrm_backend/exceptions.py

Security Middleware

Adds:

Hardened security headers

XSS & content-sniffing protection

Sanitized server error output

Location:
hcrm_backend/middleware/

Test Suite Stability

Resolved all flaky Fernet-related tests

Deterministic encryption test behavior

All 54 tests passing

🏗 Backend Project Structure
hcrm_backend/
    settings.py
    urls.py
    middleware/
    exceptions.py
    __init__.py        ← Fail-fast key validation

authentication/
appointments/
patients/
electronic_records/
    encryption.py      ← Unified Fernet implementation
    models.py
    views.py
    tests/

notifications/
audit_logs/
reporting/

tests/
    unit/
    integration/

🛠 Local Setup
1. Clone the repository
git clone <repo-url>
cd PESU_RR_CSE_A_P22_Healthcare_Appointment_and_Patient_Record_Manager_Oura-Oura

2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Create your .env file (NEVER COMMIT THIS FILE)
SECRET_KEY=<<your-django-secret>>
DEBUG=True

DB_NAME=hcrm_db
DB_USER=postgres
DB_PASSWORD=<<your-password>>
DB_HOST=localhost
DB_PORT=5432

# 32-byte url-safe base64 Fernet key
HCRM_ENCRYPTION_KEY=<<your-fernet-key>>


Generate a key:

python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

5. Load .env into PowerShell (manual loader)
Get-Content .env | ForEach-Object {
    $line = $_.Trim()
    if (-not $line.StartsWith("#") -and $line -match "=") {
        $parts = $line.Split("=", 2)
        Set-Item -Path Env:$($parts[0]) -Value $parts[1]
    }
}

6. Apply migrations
python manage.py migrate

7. Run server
python manage.py runserver

🔐 Encryption Overview
How encryption works

HCRM_ENCRYPTION_KEY loaded from environment

Key is validated before Django fully loads

All PHI & uploaded documents encrypted using Fernet (AES-128)

API
encrypt("plaintext")
decrypt("token")

encrypt_file(file_bytes)
decrypt_file(encrypted_bytes)

🧪 Running Tests
Single test (PDF upload)
pytest -q electronic_records/tests/test_document_upload.py::TestDocumentUpload::test_upload_pdf_document -vv

Full test suite
pytest -q


Expected output:

54 passed in XX.XXs

🧩 Contribution Workflow
1. Create a feature branch
git checkout -b feature/<ticket-id>-<description>

2. Make changes & run tests
3. Commit using project format
HAPRM1-19: fail-fast key validation + unified Fernet encryption

4. Push & open a PR using the project’s PR template
🔒 Security Notes

Never commit .env

Rotate secrets if exposed

CI/CD must define HCRM_ENCRYPTION_KEY

All encryption keys must be 32-byte url-safe base64 strings

📄 License

Internal project for PES University RR Campus — not for external distribution without permission.

📧 Maintainers

Team A — PESU RR Campus
Sprint ownership: Authentication, EHR, Security Middleware, Encryption Pipeline