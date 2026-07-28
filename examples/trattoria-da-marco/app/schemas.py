"""Schemi Pydantic per validazione request/response."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    name: str
    description: str = ""
    price: float = 0.0
    category: str = ""
    available: bool = True


class ItemCreate(ItemBase):
    pass


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CustomerBase(BaseModel):
    name: str
    email: str = ""
    phone: str = ""


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int = 1


class OrderItemOut(OrderItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderCreate(BaseModel):
    customer_name: str
    items: list[OrderItemCreate]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    status: str
    created_at: datetime
    items: list[OrderItemOut] = []
