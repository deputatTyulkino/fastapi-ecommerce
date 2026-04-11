from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
from sqlalchemy.sql.operators import or_

from app.auth import get_current_seller
from app.db_depends import get_db
from app.models.categories import Category
from app.models.products import Product
from app.schemas.products import ProductCreate, Product as ProductSchema, ProductList
from app.models.users import User as UserModel

router = APIRouter(
    prefix='/products',
    tags=['products']
)


@router.get('/', response_model=ProductList)
async def get_all_products(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None, min_length=1, description='Поиск по названию товара'),
        category_id: int | None = Query(None, description='ID категории для фильтрации'),
        min_price: float | None = Query(None, description='Минимальная цена товара'),
        max_price: float | None = Query(None, description='Максимальная цена товара'),
        is_stock: bool | None = Query(
            None, description='true — только товары в наличии, false — только без остатка'
        ),
        seller_id: int | None = Query(None, description='ID продавца для фильтрации'),
        db: AsyncSession = Depends(get_db)
):
    """
    Возвращает список всех товаров.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='min_price не может быть больше max_price'
        )
    filters = [Product.is_active == True]
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if seller_id is not None:
        filters.append(Product.seller_id == seller_id)
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)
    if is_stock is not None:
        filters.append(Product.stock > 0 if is_stock else Product.stock == 0)

    total_stmt = select(func.count()).select_from(Product).where(*filters)

    rank_col = None
    if search:
        search_value = search.strip()
        if search_value:
            ts_query_en = func.websearch_to_tsquery('english', search_value)
            ts_query_ru = func.websearch_to_tsquery('russian', search_value)
            ts_query = or_(
                Product.tsv.op('@@')(ts_query_en),
                Product.tsv.op('@@')(ts_query_ru)
            )
            filters.append(ts_query)
            rank_col = func.greatest(
                func.ts_rank_cd(Product.tsv, ts_query_en),
                func.ts_rank_cd(Product.tsv, ts_query_ru)
            ).label('rank')
            total_stmt = select(func.count()).select_from(Product).where(*filters)

    total = await db.scalar(total_stmt) or 0

    if rank_col is not None:
        products_stmt = (await db.scalars(
            select(Product, rank_col)
            .where(*filters)
            .order_by(desc(rank_col), Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).all()
        products = [pr[0] for pr in products_stmt]
    else:
        products = (await db.scalars(
            select(Product)
            .where(*filters)
            .order_by(Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).all()
    return {
        'items': products,
        'total': total,
        'page': page,
        'page_size': page_size
    }


@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
        product: ProductCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_seller)
):
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
    db_product = Product(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
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
async def update_product(
        product_id: int,
        product: ProductCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_seller)
):
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
    if not db_product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You can only update your own products'
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
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
        product_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_seller)
):
    """
    Удаляет товар по его ID.
    """
    stmt = await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    db_product = stmt.first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not db_product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You can only delete your own products'
        )
    await db.execute(
        update(Product).where(Product.id == product_id).values(is_active=False)
    )
    await db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
