from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db_depends import get_db
from app.models.categories import Category
from app.models.products import Product
from app.schemas.products import ProductCreate, Product as ProductSchema

router = APIRouter(
    prefix='/products',
    tags=['products']
)


@router.get('/', response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = await db.scalars(
        select(Product).where(Product.is_active == True)
    )
    products = stmt.all()
    return products


@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    stmt = await db.scalars(
        select(Category).where(
            Category.id == product.category_id, Category.is_active == True
        )
    )
    bd_category = stmt.first()
    if not bd_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive'
        )
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    return db_product


@router.get('/{product_id}', response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    stmt = await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    db_product = stmt.first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive'
        )
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    stmt = await db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    )
    db_category = stmt.first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found or inactive'
        )
    stmt_products = await db.scalars(
        select(Product).where(
            Product.category_id == category_id, Product.is_active == True
        )
    )
    products = stmt_products.all()
    return products


@router.put("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    stmt = await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    db_product = stmt.first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive'
        )
    stmt_db_category = await db.scalars(
        select(Category).where(
            Category.id == db_product.category_id, Category.is_active == True
        )
    )
    db_category = stmt_db_category.first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive'
        )
    await db.execute(
        update(Product).where(Product.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Удаляет товар по его ID.
    """
    stmt = await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    db_product = stmt.first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.execute(
        update(Product).where(Product.id == product_id).values(is_active=False)
    )
    await db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
