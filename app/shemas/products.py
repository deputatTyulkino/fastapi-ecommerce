from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=100, description='Название товара')
    description: str | None = Field(None, max_length=500, description='Описание товара')
    price: Decimal = Field(gt=0, decimal_places=2, description='Цена товара')
    image_url: str | None = Field(None, max_length=200, description='URL изображения товара')
    stock: int = Field(ge=0, description='Количество товара на складе')
    category_id: int = Field(description='ID категории, к которой относится товар')


class Product(BaseModel):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: int = Field(description='Уникальный идентификатор товара')
    name: str = Field(description='Название товара')
    description: str | None = Field(None, description='Описание товара')
    price: Decimal = Field(gt=0, decimal_places=2, description='Цена товара в рублях')
    image_url: str | None = Field(None, description='URL изображения товара')
    stock: int = Field(description='Количество товара на складе')
    category_id: int = Field(description='ID категории')
    is_active: bool = Field(description='Активность товара')
    model_config = ConfigDict(from_attributes=True)
