from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import UniqueConstraint, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

if TYPE_CHECKING:
    from .users import User
    from .products import Product


class CartItem(BaseModel):
    __tablename__ = 'cart_items'

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_cart_items_user_product')
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now()
    )

    user: Mapped['User'] = relationship('User', back_populates='cart_items')
    product: Mapped['Product'] = relationship('Product', back_populates='cart_items')
