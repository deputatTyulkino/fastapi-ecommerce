from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db_depends import get_db
from app.schemas.categories import CategorySchema, CategoryCreate
from app.models.categories import Category

router = APIRouter(
    prefix='/categories',
    tags=['categories']
)


@router.get('/', response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """
    Возвращает список всех категорий товаров.
    """
    stmt = await db.scalars(
        select(Category).where(Category.is_active == True)
    )
    categories = stmt.all()
    return categories


@router.post('/', response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        stmt = await db.scalars(
            select(Category)
            .where(Category.id == category.parent_id, Category.is_active == True)
        )
        parent = stmt.first()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Parent category not found'
            )
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    return db_category


@router.put('/{category_id}', response_model=CategorySchema)
async def update_category(
        category_id: int, category: CategoryCreate, db: AsyncSession = Depends(get_db)
):
    """
    Обновляет категорию по её ID.
    """
    stmt = await db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    )
    db_category = stmt.first()
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found'
        )
    if category.parent_id is not None:
        parent_stmt = await db.scalars(
            select(Category).where(
                Category.id == category.parent_id, Category.is_active == True
            )
        )
        parent = parent_stmt.first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Parent category not found'
            )
        if parent.id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Category cannot be its own parent'
            )
    updated_data = category.model_dump(exclude_unset=True)
    await db.execute(
        update(Category)
        .where(Category.id == category_id)
        .values(**updated_data)
    )
    await db.commit()
    return db_category


@router.delete('/{category_id}', status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Удаляет категорию по её ID.
    """
    stmt = await db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    )
    category = stmt.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found'
        )
    await db.execute(
        update(Category).where(Category.id == category_id).values(is_active=False)
    )
    await db.commit()
    return {"status": "success", "message": "Category marked as inactive"}
