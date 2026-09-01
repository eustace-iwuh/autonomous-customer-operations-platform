from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.security.jwt import create_access_token
from backend.security.passwords import verify_password
from backend.services.auth_service import AuthService
from backend.api.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    try:
        user = service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )

        db.commit()
        db.refresh(user)

        return user

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    user = service.get_user_by_email(request.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

    
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user