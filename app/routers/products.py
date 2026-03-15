from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    products = db.scalars(
        select(Product).where(Product.is_active == True)
    ).all()
    if products is None:
        return []
    return products


@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    if product.category_id is not None:
        bd_category = db.scalars(
            select(Category).where(
                Category.id == product.category_id, Category.is_active == True
            )
        ).first()
        if bd_category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive'
            )
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get('/{product_id}', response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    db_product = db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    ).first()
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive'
        )
    bd_category = db.scalars(
        select(Category).where(
            Category.id == db_product.category_id, Category.is_active == True
        )
    ).first()
    if bd_category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive'
        )
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    db_category = db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    ).first()
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found or inactive'
        )
    products = db.scalars(
        select(Product).where(Product.category_id == category_id, Product.is_active == True)
    ).all()
    return products


@router.put("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    db_product = db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    ).first()
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive'
        )
    db_category = db.scalars(
        select(Category).where(
            Category.id == db_product.category_id, Category.is_active == True
        )
    ).first()
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive'
        )
    db.execute(
        update(Product).where(Product.id == product_id).values(**product.model_dump())
    )
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Удаляет товар по его ID.
    """
    db_product = db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    ).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.execute(
        update(Product).where(Product.id == product_id).values(is_active=False)
    )
    db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
