from decimal import Decimal
from typing import TYPE_CHECKING

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Numeric, Boolean, ForeignKey

if TYPE_CHECKING:
    from .categories import Category
    from .users import User


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200))
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    category: Mapped["Category"] = relationship(
        "Category", back_populates='products'
    )
    seller: Mapped['User'] = relationship('User', back_populates='products')
