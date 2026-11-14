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
from fastapi.responses import HTMLResponse
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
    
    stmt = (
        update(User)
        .where(User.id == current_user.id)
        .values(avatar=avatar_url)
    )
    await db.execute(stmt)
    await db.commit()

    # Видаляємо старий кеш користувача з Redis
    await redis_client.delete(f"user:{current_user.email}")

    current_user.avatar = avatar_url
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


@router.get("/reset-password-page/{token}", response_class=HTMLResponse, include_in_schema=False)
async def reset_password_page(token: str):
    # Перевіряємо валідність токена ще до показу форми
    payload = decode_token(token, expected_scope="reset_password")
    if payload is None:
        return HTMLResponse(
            content="<h3>Посилання недійсне або термін його дії закінчився.</h3>", 
            status_code=400
        )

    return f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Скидання пароля</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center vh-100">
        <div class="container" style="max-width: 420px;">
            <div class="card shadow-sm p-4">
                <h4 class="text-center mb-3">Новий пароль</h4>
                <div class="mb-3">
                    <label class="form-label">Введіть новий пароль (мін. 6 символів)</label>
                    <input type="password" id="newPassword" class="form-control" required minlength="6">
                </div>
                <button onclick="submitNewPassword()" class="btn btn-primary w-100">Зберегти пароль</button>
                <div id="msg" class="alert mt-3 d-none"></div>
            </div>
        </div>

        <script>
            async function submitNewPassword() {{
                const newPassword = document.getElementById("newPassword").value;
                const msgDiv = document.getElementById("msg");

                const res = await fetch("/auth/reset-password", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{
                        token: "{token}",
                        new_password: newPassword
                    }})
                }});

                const data = await res.json();
                msgDiv.classList.remove("d-none", "alert-danger", "alert-success");

                if (res.ok) {{
                    msgDiv.classList.add("alert-success");
                    msgDiv.innerText = data.message + " Перенаправлення на вхід...";
                    setTimeout(() => window.location.href = "/", 2000);
                }} else {{
                    msgDiv.classList.add("alert-danger");
                    msgDiv.innerText = data.detail || "Помилка при зміні пароля";
                }}
            }}
        </script>
    </body>
    </html>
    """

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(body.token, expected_scope="reset_password")
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