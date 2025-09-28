from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.schemas import UserCreate, UserOut, LoginIn, Token
from app.db.crud import create_user, authenticate, get_user_by_email
from app.db.models import UserRole
from app.db.session import get_db
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    exists = await get_user_by_email(db, payload.email)
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, payload.email, payload.password, UserRole(payload.role))
    return user

@router.post("/login", response_model=Token)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    token = create_access_token(sub=user.email)
    return {"access_token": token, "token_type": "bearer"}
