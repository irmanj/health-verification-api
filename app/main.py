import hashlib
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import (
    VerificationRequestCreate,
    VerificationRequestResponse,
    ConsentDecisionCreate,
    OTPVerifyCreate,
)

from datetime import datetime, timezone, timedelta

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health Verification API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post(
    "/verification-requests",
    response_model=VerificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_verification_request(
    request: VerificationRequestCreate,
    db: Session = Depends(get_db),
):
    verification = models.VerificationRequest(
        patient_id=request.patient_id,
        purpose=request.purpose,
    )

    try:
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return verification
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save verification request",
        )

@app.post(
    "/verification-requests/{request_id}/consent",
    response_model=VerificationRequestResponse,
)
def submit_consent(
    request_id: str,
    decision: ConsentDecisionCreate,
    db: Session = Depends(get_db),
):
    verification = db.get(models.VerificationRequest, request_id)

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification request not found",
        )

    if verification.otp_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="OTP must be verified before consent",
        )

    if verification.status != "PENDING_CONSENT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consent has already been decided",
        )

    verification.status = (
        "CONSENTED" if decision.approved else "CONSENT_REJECTED"
    )
    verification.consent_decided_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(verification)
        return verification
    except SQLAlchemyError as e:
        db.rollback()
        print("DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save verification request",
        )

@app.post("/verification-requests/{request_id}/generate-otp")
def generate_otp(
    request_id: str,
    db: Session = Depends(get_db),
):
    verification = db.get(models.VerificationRequest, request_id)

    if verification is None:
        raise HTTPException(status_code=404, detail="Request not found")

    if verification.status != "PENDING_CONSENT":
        raise HTTPException(
            status_code=409,
            detail="Request is not waiting for consent",
        )

    otp = f"{secrets.randbelow(1000000):06d}"

    verification.otp_hash = hashlib.sha256(
        otp.encode()
    ).hexdigest()

    verification.otp_expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    try:
        db.commit()
        return {
            "message": "OTP generated successfully",
            "otp": otp,
            "expires_in_minutes": 5,
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate OTP",
        )

@app.post("/verification-requests/{request_id}/verify-otp")
def verify_otp(
    request_id: str,
    payload: OTPVerifyCreate,
    db: Session = Depends(get_db),
):
    verification = db.get(models.VerificationRequest, request_id)

    if verification is None:
        raise HTTPException(status_code=404, detail="Request not found")

    if verification.status != "PENDING_CONSENT":
        raise HTTPException(status_code=409, detail="Invalid request status")

    if verification.otp_hash is None or verification.otp_expires_at is None:
        raise HTTPException(status_code=400, detail="OTP has not been generated")

    now = datetime.now(timezone.utc)

    if verification.otp_expires_at <= now:
        raise HTTPException(status_code=400, detail="OTP has expired")

    submitted_hash = hashlib.sha256(payload.otp.encode()).hexdigest()

    if not secrets.compare_digest(
        verification.otp_hash,
        submitted_hash,
    ):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    verification.otp_verified_at = now

    try:
        db.commit()
        return {"message": "OTP verified successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

@app.post("/verification-requests/{request_id}/verify-bpjs")
def verify_bpjs(
    request_id: str,
    db: Session = Depends(get_db),
):
    verification = db.get(models.VerificationRequest, request_id)

    if verification is None:
        raise HTTPException(status_code=404, detail="Request not found")

    if verification.status != "CONSENTED":
        raise HTTPException(
            status_code=403,
            detail="Patient consent is required before BPJS verification",
        )

    # simulasi pengecekan kepesertaan BPJS
    verification.bpjs_registered = verification.patient_id == "1"
    verification.bpjs_checked_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(verification)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save BPJS verification result",
        )

    return {
        "request_id": verification.id,
        "patient_id": verification.patient_id,
        "bpjs_registered": verification.bpjs_registered,
        "bpjs_checked_at": verification.bpjs_checked_at,
        "message": (
            "Patient is registered with BPJS"
            if verification.bpjs_registered
            else "Patient is not registered with BPJS"
        ),
    }