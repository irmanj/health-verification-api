from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class VerificationRequestCreate(BaseModel):
  patient_id: str = Field(min_length=1, max_length=100)
  purpose: str = Field(min_length=5)

class VerificationRequestResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: str
  patient_id: str
  purpose: str
  status: str
  created_at: datetime

class ConsentDecisionCreate(BaseModel):
  approved: bool

class OTPVerifyCreate(BaseModel):
  otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")