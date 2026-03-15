from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.db_depends import get_db
from app.schemas.categories import CategorySchema, CategoryCreate
from app.models.categories import Category

router = APIRouter(
    prefix='/categories',
    tags=['categories']
)


@router.get('/', response_model=list[CategorySchema])
async def get_all_categories(db: Session = Depends(get_db)):
    """
    Возвращает список всех категорий товаров.
    """
    categories = db.scalars(
        select(Category).where(Category.is_active == True)
    ).all()
    return categories


@router.post('/', response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        parent = db.scalars(
            select(Category)
            .where(Category.id == category.parent_id, Category.is_active == True)
        ).first()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Parent category not found'
            )
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put('/{category_id}', response_model=CategorySchema)
async def update_category(
        category_id: int, category: CategoryCreate, db: Session = Depends(get_db)
) -> dict:
    """
    Обновляет категорию по её ID.
    """
    db_category = db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    ).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found'
        )
    if category.parent_id is not None:
        parent = db.scalars(
            select(Category).where(
                Category.id == category.parent_id, Category.is_active == True
            )
        ).first()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Parent category not found'
            )
    db.execute(
        update(Category)
        .where(Category.id == category_id)
        .values(**category.model_dump())
    )
    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete('/{category_id}', status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Удаляет категорию по её ID.
    """
    category = db.scalars(
        select(Category).where(Category.id == category_id, Category.is_active == True)
    ).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Category not found'
        )
    db.execute(
        update(Category).where(Category.id == category_id).values(is_active=False)
    )
    db.commit()
    return {"status": "success", "message": "Category marked as inactive"}
