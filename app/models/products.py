from decimal import Decimal
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy.dialects.postgresql import TSVECTOR

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Numeric, Boolean, ForeignKey, DateTime, func, Computed, Index

if TYPE_CHECKING:
    from .categories import Category
    from .users import User
    from .reviews import Review
    from .cart_items import CartItem


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200))
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(1, 1), default=0.0)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tsv: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            '''
            setweight(to_tsvector('english', coalesce(name, '')), 'A')
            ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
            ||
            setweight(to_tsvector('russian', coalesce(name, '')), 'A')
            ||
            setweight(to_tsvector('russian', coalesce(description, '')), 'B')
            ''',
            persisted=True
        ),
        nullable=False
    )

    category: Mapped["Category"] = relationship(
        "Category", back_populates='products'
    )
    seller: Mapped['User'] = relationship('User', back_populates='products')
    reviews: Mapped['Review'] = relationship('Review', back_populates='product')
    cart_item: Mapped['CartItem'] = relationship(
        'CartItem', back_populates='product', cascade='all, delete-orphan'
    )

    __table_args__ = (
        Index('idx_products_tsv_gin', 'tsv', postgresql_using='gin'),
    )
