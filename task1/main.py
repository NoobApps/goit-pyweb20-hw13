import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import engine, Base
from logger import logger
from auth.router import router as auth_router
from contacts.router import router as contacts_router


limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Додаток успішно запущено.")
    yield
    logger.info("Зупинка додатка...")


app = FastAPI(
    title="Contacts REST API",
    description="Управління контактами з верифікацією пошти, CORS, Cloudinary та Rate Limiting.",
    version="3.0.0",
    lifespan=lifespan
)

# Підключення Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Увімкнення CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можна вказати списком конкретні домени: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення роутерів
app.include_router(auth_router)
app.include_router(contacts_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)