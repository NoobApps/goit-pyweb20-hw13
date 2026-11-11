from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
from database import get_db
from database_redis import redis_client
from auth.auth import decode_token
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося валідувати токен авторизації",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token, expected_scope="access")
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # 1. Спроба отримати користувача з кешу Redis
    cache_key = f"user:{email}"
    user_data = await redis_client.get(cache_key)

    if user_data:
        # Створюємо об'єкт User з даних кешу
        user_dict = json.loads(user_data)
        user = User(**user_dict)
    else:
        # 2. Якщо в кеші немає — шукаємо в PostgreSQL
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        # Зберігаємо дані користувача у кеш Redis на 1800 секунд (30 хвилин)
        cached_user_info = {
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "confirmed": user.confirmed,
            "avatar": user.avatar
        }
        await redis_client.set(cache_key, json.dumps(cached_user_info), ex=1800)

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна пошта не підтверджена"
        )
        
    return user