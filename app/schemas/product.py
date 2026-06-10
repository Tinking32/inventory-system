from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Wireless Mouse"])
    description: str = Field(default="", max_length=500)
    quantity: int = Field(..., ge=0, examples=[100])
    price: float = Field(..., ge=0.0, examples=[29.99])
    low_stock_threshold: int = Field(default=20, ge=0)
    category_id: Optional[int] = Field(default=None)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    quantity: Optional[int] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0.0)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = Field(default=None)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    quantity: int
    price: float
    low_stock_threshold: int
    category_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_low_stock: bool

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
