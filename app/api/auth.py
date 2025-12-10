"""
Authentication Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.provider import Provider
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, AuthResponseWithUser
from app.schemas.provider import ProviderCreate, ProviderResponse, AuthResponseWithProvider
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register/user", response_model=AuthResponseWithUser, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user (homeowner)"""
    # Check if email exists
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = AuthService.get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "user"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register/provider", response_model=AuthResponseWithProvider, status_code=status.HTTP_201_CREATED)
async def register_provider(
    provider_data: ProviderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new provider (gig worker)"""
    # Check if email exists
    query = select(Provider).where(Provider.email == provider_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create provider
    hashed_password = AuthService.get_password_hash(provider_data.password)
    provider = Provider(
        email=provider_data.email,
        hashed_password=hashed_password,
        full_name=provider_data.full_name,
        phone=provider_data.phone,
        job_types=provider_data.job_types,
        hourly_rate=provider_data.hourly_rate
    )
    
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": provider.email, "user_id": provider.id, "user_type": "provider"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": provider
    }


@router.post("/login/user", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login as user (accepts form data)"""
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": user.email, "user_id": user.id, "user_type": "user"}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/provider", response_model=Token)
async def login_provider(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login as provider (accepts form data)"""
    query = select(Provider).where(Provider.email == form_data.username)
    result = await db.execute(query)
    provider = result.scalar_one_or_none()
    
    if not provider or not AuthService.verify_password(form_data.password, provider.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": provider.email, "user_id": provider.id, "user_type": "provider"}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
