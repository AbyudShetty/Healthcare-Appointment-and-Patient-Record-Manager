# 🏥 Electronic Records – Secure History API & Encryption (Sprint 1 Deliverable)

**Author:** Pranav (AP)
**Module:** Electronic Records
**Sprint:** 1 (Backend Tasks)
**Date:** November 2025

---

## 📋 Overview

This module implements **secure access** to patient medical records and clinical notes.
It introduces **AES-based encryption/decryption** of sensitive data fields and exposes a protected API endpoint for viewing patient history, with full **JWT authentication** and **role-based access control**.

---

## 🚀 Features Implemented

### 🔐 Data Encryption

* Added `encrypt_field` and `decrypt_field` in `electronic_records/utils.py` using **Fernet (AES-128-CBC)**.
* Automatically encrypts:

  * `PatientRecord.medical_history_encrypted`
  * `PatientRecord.diagnoses_encrypted`
  * `PatientRecord.medications_encrypted`
  * `ClinicalNote.note_content_encrypted`
* Decrypts securely on read or via serializers.

### 🧠 Secure History API

* **Endpoint:** `/api/v1/records/<patient_id>/history/`
* **View:** `SecureHistoryView`
* **Serializer:** `PatientRecordSerializer` and `ClinicalNoteSerializer`
* **Access Rules:**

  * ✅ Clinician/Admin → Can view any patient’s records.
  * ✅ Patient → Can only view their own records.
  * ⛔ Others/Unauthenticated → Denied (403/401).
* Includes decrypted notes (`decrypted_note`) in the response.

### 🤪 Automated Tests

Located in `electronic_records/tests/`:

1. `test_encryption.py` → Validates encryption/decryption logic.
2. `test_secure_history_api.py` → Validates API authentication, role-based access, and decrypted response content.

All tests pass successfully ✅

---

## ⚙️ How to Run Locally

### 1️⃣ Prerequisites

* Python 3.11+
* PostgreSQL (configured as per `settings.py`)
* Virtual environment (recommended)
* Django & DRF installed

### 2️⃣ Setup & Activate Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ Set the Encryption Key (Fernet)

Generate a key once:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

Then set it in PowerShell (before running server/tests):

```powershell
$env:MY_FERNET_KEY = "PASTE_YOUR_KEY_HERE"
```

---

## 🧰 Run the Server

```bash
python manage.py runserver
```

Now visit:

```
http://127.0.0.1:8000/api/v1/records/<patient_id>/history/
```

Use JWT tokens for authentication (via `/api/v1/auth/login/`).

---

## 🤪 Run Tests

Run the complete test suite or specific files:

```bash
python manage.py test
# or
python manage.py test electronic_records.tests.test_encryption
python manage.py test electronic_records.tests.test_secure_history_api
```

Expected output:

```
....
----------------------------------------------------------------------
Ran 6 tests in X.XXXs
OK
```

---

## 🗾 Example Auth + API Call (PowerShell)

```powershell
# Login and get JWT
$body = @{ username = "admin"; password = "your_password" } | ConvertTo-Json
$response = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/auth/login/" -Body $body -ContentType 'application/json'
$token = $response.access
$headers = @{ "Authorization" = "Bearer $token" }

# Fetch patient record history
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/records/PAT000001/history/" -Headers $headers | ConvertTo-Json -Depth 10
```

Sample response:

```json
{
  "count": 1,
  "results": [
    {
      "medical_history": "Test history A",
      "diagnoses": "Test Dx A",
      "medications": "Test med A",
      "clinical_notes": [
        {
          "id": 1,
          "clinician": "admin",
          "decrypted_note": "Initial consultation note: Blood pressure normal."
        }
      ]
    }
  ]
}
```

---

## 🧱 Folder Structure (Relevant Files)

```
electronic_records/
│
├── models.py
├── serializers.py
├── views.py
├── utils.py
├── urls.py
└── tests/
    ├── test_encryption.py
    └── test_secure_history_api.py
```

---

## 🧑‍💻 Developer Notes

* All sensitive fields now stored encrypted in DB.
* `MY_FERNET_KEY` must remain consistent per environment.
* Tests use dynamically generated key for isolation.
* **Next sprint (handled by other team members):**

  * Frontend integration
  * Logging/auditing of access
  * Environment-secure key storage (Vault or .env)
  * Deployment setup for production (DEBUG=False)

---

✅ **Status:** Completed and verified
📦 **Ready
