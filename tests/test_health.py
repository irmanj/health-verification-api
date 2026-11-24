from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app import models
from app.database import SessionLocal

client = TestClient(app)


def test_health_cek():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_verification_request():
    response = client.post(
        "/verification-requests",
        json={
            "patient_id": "TEST-001",
            "purpose": "BPJS eligibility verification"
        }
    )

    assert response.status_code == 201
    assert response.json()["patient_id"] == "TEST-001"
    assert response.json()["status"] == "PENDING_CONSENT"

def test_verify_otp_success():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "OTP-001",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    otp_response = client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    otp = otp_response.json()["otp"]

    verify_response = client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": otp}
    )

    assert verify_response.status_code == 200
    assert verify_response.json()["message"] == "OTP verified successfully"


def test_verify_otp_wrong():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "OTP-002",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    verify_response = client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": "000000"}
    )

    assert verify_response.status_code == 400
    assert verify_response.json()["detail"] == "Invalid OTP"

def test_verify_otp_expired():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "OTP-003",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    db = SessionLocal()
    try:
        verification = db.get(
            models.VerificationRequest,
            request_id
        )

        verification.otp_expires_at = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        )

        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": "123456"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "OTP has expired"

def test_consent_without_otp():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "CONSENT-001",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    response = client.post(
        f"/verification-requests/{request_id}/consent",
        json={"approved": True}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "OTP must be verified before consent"

def test_consent_approved():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "CONSENT-002",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    otp_response = client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    otp = otp_response.json()["otp"]

    client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": otp}
    )

    response = client.post(
        f"/verification-requests/{request_id}/consent",
        json={"approved": True}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONSENTED"

def test_consent_rejected():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "CONSENT-003",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    otp_response = client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    otp = otp_response.json()["otp"]

    client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": otp}
    )

    response = client.post(
        f"/verification-requests/{request_id}/consent",
        json={"approved": False}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONSENT_REJECTED"

def test_bpjs_without_consent():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "BPJS-001",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    response = client.post(
        f"/verification-requests/{request_id}/verify-bpjs"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Patient consent is required before BPJS verification"
    )

def test_bpjs_registered():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "1",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    otp_response = client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    otp = otp_response.json()["otp"]

    client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": otp}
    )

    client.post(
        f"/verification-requests/{request_id}/consent",
        json={"approved": True}
    )

    response = client.post(
        f"/verification-requests/{request_id}/verify-bpjs"
    )

    assert response.status_code == 200
    assert response.json()["bpjs_registered"] is True
    assert response.json()["patient_id"] == "1"

def test_bpjs_not_registered():
    create_response = client.post(
        "/verification-requests",
        json={
            "patient_id": "2",
            "purpose": "BPJS eligibility verification"
        }
    )

    request_id = create_response.json()["id"]

    otp_response = client.post(
        f"/verification-requests/{request_id}/generate-otp"
    )

    otp = otp_response.json()["otp"]

    client.post(
        f"/verification-requests/{request_id}/verify-otp",
        json={"otp": otp}
    )

    client.post(
        f"/verification-requests/{request_id}/consent",
        json={"approved": True}
    )

    response = client.post(
        f"/verification-requests/{request_id}/verify-bpjs"
    )

    assert response.status_code == 200
    assert response.json()["bpjs_registered"] is False
    assert response.json()["patient_id"] == "2"