from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from contacts.schemas import ContactCreate, ContactUpdate, ContactResponse
from auth.dependencies import get_current_user
from models import User
import contacts.crud as crud

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Обмеження: 5 запитів на хвилину
async def create_contact(
    request: Request,
    contact: ContactCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.create_contact(db, contact, current_user.id)


@router.get("/", response_model=list[ContactResponse])
async def read_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    query: str | None = Query(None, description="Пошук за ім'ям, прізвищем або email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit, query=query)


@router.get("/upcoming-birthdays", response_model=list[ContactResponse])
async def upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.get_upcoming_birthdays(db, user_id=current_user.id, days=7)


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = await crud.get_contact_by_id(db, contact_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int, 
    contact: ContactUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_contact = await crud.update_contact(db, contact_id, contact, current_user.id)
    if not updated_contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return updated_contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = await crud.delete_contact(db, contact_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено")
    return None