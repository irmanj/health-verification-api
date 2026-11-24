import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class VerificationRequest(Base):
  __tablename__ = "verification_requests"

  id: Mapped[str] = mapped_column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4()),
  )
  patient_id: Mapped[str] = mapped_column(String(100), nullable=False)
  purpose: Mapped[str] = mapped_column(Text, nullable=False)
  status: Mapped[str] = mapped_column(
      String(30),
      nullable=False,
      default="PENDING_CONSENT",
  )
  created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      default=datetime.utcnow,
      nullable=False,
  )
  consent_decided_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
  )
  otp_hash: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True
  )

  otp_expires_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
  )

  otp_verified_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
  )

  bpjs_registered: Mapped[bool | None] = mapped_column(
    Boolean,
    nullable=True,
  )

  bpjs_checked_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
  )