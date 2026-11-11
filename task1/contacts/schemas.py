from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional


class ContactBase(BaseModel):
    first_name: str = Field(..., max_length=50, example="Іван")
    last_name: str = Field(..., max_length=50, example="Пархоменко")
    email: EmailStr = Field(..., example="ivan@example.com")
    phone: str = Field(..., max_length=20, example="+380971234567")
    birthday: date = Field(..., example="1995-05-15")
    additional_data: Optional[str] = Field(None, example="Колега по роботі")


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    birthday: Optional[date] = None
    additional_data: Optional[str] = None


class ContactResponse(ContactBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True