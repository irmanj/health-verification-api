# Health Verification API

A backend REST API built with FastAPI and PostgreSQL to manage patient verification requests, OTP validation, patient consent, and BPJS membership verification.

## Features

- Create patient verification requests
- Generate six-digit OTP codes
- Verify OTP codes with expiration handling
- Store OTP hashes instead of plaintext OTPs
- Manage patient consent (approved or rejected)
- Validate consent before BPJS verification
- Store BPJS verification results and timestamps
- Automated testing with Pytest

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Pytest

## Verification Workflow

1. An insurance provider creates a verification request.
2. The system generates an OTP.
3. The patient verifies the OTP.
4. The patient approves or rejects consent.
5. The system checks BPJS membership eligibility.
6. The verification result is stored in PostgreSQL.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/verification-requests` | Create verification request |
| POST | `/verification-requests/{request_id}/generate-otp` | Generate OTP |
| POST | `/verification-requests/{request_id}/verify-otp` | Verify OTP |
| POST | `/verification-requests/{request_id}/consent` | Submit patient consent |
| POST | `/verification-requests/{request_id}/verify-bpjs` | Verify BPJS membership |

## Run Locally

Clone the repository:

```bash
git clone https://github.com/irmanj/health-verification-api
cd health-verification-api
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the PostgreSQL database:

```sql
CREATE DATABASE health_verification_db;
```

Run the application:

```bash
uvicorn app.main:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

## Automated Testing

Run tests:

```bash
python -m pytest -v
```

Current test result: **11 passed**.

## Important Notes

- BPJS membership verification currently uses a local simulation, not a real BPJS integration.
- The OTP response exposes the generated code for development and testing purposes only.
- Production deployment requires secure OTP delivery, proper secret management, and integration with an authorized BPJS service.

## Project Status

Core API workflow and automated tests have been implemented.