from decimal import Decimal

from fastapi.params import Form
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.sql.annotation import Annotated


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=3, max_length=100, description='Название товара')
    description: str | None = Field(None, max_length=500, description='Описание товара')
    price: Decimal = Field(..., gt=0, decimal_places=2, description='Цена товара')
    stock: int = Field(..., ge=0, description='Количество товара на складе')
    category_id: int = Field(..., description='ID категории, к которой относится товар')

    @classmethod
    def as_form(
            cls,
            name: Annotated[str, Form(...)],
            price: Annotated[Decimal, Form(...)],
            stock: Annotated[int, Form(...)],
            category_id: Annotated[int, Form(...)],
            description: Annotated[str | None, Form()] = None
    ):
        return cls(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id
        )


class Product(BaseModel):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: int = Field(..., description='Уникальный идентификатор товара')
    name: str = Field(..., description='Название товара')
    description: str | None = Field(None, description='Описание товара')
    price: Decimal = Field(..., gt=0, decimal_places=2, description='Цена товара в рублях')
    image_url: str | None = Field(None, description='URL изображения товара')
    stock: int = Field(..., description='Количество товара на складе')
    category_id: int = Field(..., description='ID категории')
    is_active: bool = Field(..., description='Активность товара')
    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """
    Список пагинации для товаров.
    """
    items: list[Product] = Field(description='Товары для текущей страницы')
    total: int = Field(ge=0, description='Общее количество товаров')
    page: int = Field(ge=1, description='Номер текущей страницы')
    page_size: int = Field(ge=1, description='Количество элементов на странице')
    model_config = ConfigDict(from_attributes=True)
