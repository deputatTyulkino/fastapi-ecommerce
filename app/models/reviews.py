from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, Boolean, Text

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .users import User
from .products import Product


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    comment = mapped_column(Text)
    comment_date: Mapped[datetime] = mapped_column(default=datetime.now)
    grade: Mapped[int]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped['User'] = relationship(User, back_populates='reviews')
    product: Mapped['Product'] = relationship(Product, back_populates='reviews')
