from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, extract, and_
from datetime import date, timedelta
from models import Contact
from contacts.schemas import ContactCreate, ContactUpdate
from logger import logger


async def create_contact(db: AsyncSession, contact_data: ContactCreate, user_id: int) -> Contact:
    contact = Contact(**contact_data.model_dump(), user_id=user_id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    logger.info(f"Створено контакт ID={contact.id} для користувача ID={user_id}")
    return contact


async def get_contacts(
    db: AsyncSession, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100, 
    query: str | None = None
) -> list[Contact]:
    stmt = select(Contact).where(Contact.user_id == user_id)
    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                Contact.email.ilike(search_pattern)
            )
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contact_by_id(db: AsyncSession, contact_id: int, user_id: int) -> Contact | None:
    stmt = select(Contact).where(and_(Contact.id == contact_id, Contact.user_id == user_id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_contact(db: AsyncSession, contact_id: int, contact_data: ContactUpdate, user_id: int) -> Contact | None:
    contact = await get_contact_by_id(db, contact_id, user_id)
    if not contact:
        return None
    
    update_dict = contact_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(contact, key, value)

    await db.commit()
    await db.refresh(contact)
    logger.info(f"Оновлено контакт ID={contact_id} користувача ID={user_id}")
    return contact


async def delete_contact(db: AsyncSession, contact_id: int, user_id: int) -> Contact | None:
    contact = await get_contact_by_id(db, contact_id, user_id)
    if not contact:
        return None
    
    await db.delete(contact)
    await db.commit()
    logger.info(f"Видалено контакт ID={contact_id} користувача ID={user_id}")
    return contact


async def get_upcoming_birthdays(db: AsyncSession, user_id: int, days: int = 7) -> list[Contact]:
    today = date.today()
    upcoming_dates = [(today + timedelta(days=i)) for i in range(days + 1)]
    date_conditions = [
        and_(
            extract('month', Contact.birthday) == d.month,
            extract('day', Contact.birthday) == d.day
        )
        for d in upcoming_dates
    ]
    
    stmt = select(Contact).where(
        and_(
            Contact.user_id == user_id,
            or_(*date_conditions)
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())