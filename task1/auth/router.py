from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    UploadFile,
    File,
    BackgroundTasks
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database_redis import redis_client
from models import User
from logger import logger
from auth.schemas import (
    UserCreate, 
    UserResponse, 
    TokenResponse, 
    RefreshTokenRequest,
    RequestResetPasswordSchema,  
    ResetPasswordSchema
)
from auth.auth import verify_password, get_password_hash, create_tokens, decode_token
from auth.email import send_verification_email,send_reset_password_email
from auth.avatar import upload_avatar
from auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує"
        )
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_pwd, confirmed=False)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Відправка листа у фоновому режимі
    background_tasks.add_task(send_verification_email, new_user.email, str(request.base_url))
    return new_user


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(token, expected_scope="access")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний токен підтвердження")
    
    email = payload.get("sub")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Користувача не знайдено")
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}

    user.confirmed = True
    await db.commit()
    return {"message": "Електронну пошту успішно підтверджено!"}


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний email або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна пошта не підтверджена"
        )

    return create_tokens(data={"sub": user.email})

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def refresh_tokens(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token, expected_scope="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний або прострочений refresh token"
        )
    
    email = payload.get("sub")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача не знайдено"
        )
        
    return create_tokens(data={"sub": user.email})


@router.patch("/avatar", response_model=UserResponse)
async def update_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    avatar_url = upload_avatar(file.file, public_id=str(current_user.id))
    current_user.avatar = avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/request-reset-password")
async def request_reset_password(
    body: RequestResetPasswordSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == body.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        background_tasks.add_task(send_reset_password_email, user.email, str(request.base_url))

    return {"message": "Якщо вказана адреса існує в системі, ми надіслали інструкції для скидання пароля на вашу пошту."}

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(body.token, expected_scope="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Недійсний або прострочений токен"
        )
    
    email = payload.get("sub")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Користувача не знайдено"
        )

    # Оновлюємо пароль у БД
    user.hashed_password = get_password_hash(body.new_password)
    await db.commit()

    # Інвалідуємо (видаляємо) кеш користувача в Redis
    await redis_client.delete(f"user:{user.email}")

    return {"message": "Пароль успішно змінено!"}