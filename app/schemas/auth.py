from pydantic import BaseModel, EmailStr
from app.models.membership import RoleEnum

class SignupRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    org_id: str
    role: RoleEnum
    exp: int
