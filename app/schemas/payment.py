from pydantic import BaseModel, Field

from app.schemas.orders import Order


class OrderCheckoutResponse(BaseModel):
    order: Order = Field(..., description="Созданный заказ")
    confirmation_url: str | None = Field(
        None,
        description="URL для перехода на оплату в YooKassa",
    )

