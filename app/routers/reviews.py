from fastapi import APIRouter, Depends, HTTPException, status
from rest_framework.status import HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from app.models.users import User as UserModel
from app.auth import get_current_user
from app.db_depends import get_db
from app.models import Product
from app.schemas.reviews import Review as ReviewSchema, CreateReview
from app.models.reviews import Review as ReviewModel
from app.routers.products import router as products_router

reviews_router = APIRouter(
    prefix='/reviews',
    tags=['reviews']
)


async def update_grade_product(db: AsyncSession, product_id: int):
    """
    Обновляет рэйтинг товара
    """
    result = await db.scalar(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id, ReviewModel.is_active == True
        )
    )
    avg_rating = result or 0.0
    product = (await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )).first()
    product.rating = avg_rating
    await db.commit()


@reviews_router.get('/', response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_db)):
    """
    Возвращает список всех активных отзывов
    """
    reviews = (await db.scalars(
        select(ReviewModel).where(ReviewModel.is_active == True)
    )).all()
    return reviews


@products_router.get('/{product_id}/reviews', response_model=list[ReviewSchema])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает отзывы определённого товара
    """
    product = (await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product with this id not found'
        )
    reviews = (await db.scalars(
        select(ReviewModel).where(
            ReviewModel.product_id == product_id, ReviewModel.is_active == True
        )
    )).all()
    return reviews


@products_router.post('/reviews', response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
        review: CreateReview,
        user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Создаёт отзыв и возвращает его
    """
    product = (await db.scalars(
        select(Product).where(Product.id == review.product_id, Product.is_active == True)
    )).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Product with this id not found'
        )
    if user.role != 'buyer':
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail='You can`t create review'
        )
    new_review = ReviewModel(**review.model_dump(), user_id=user.id)
    db.add(new_review)
    await db.commit()
    await update_grade_product(db, product.id)
    await db.refresh(new_review)
    return new_review


@products_router.delete('/reviews/{review_id}', status_code=status.HTTP_200_OK)
async def delete_review(
        review_id: int,
        db: AsyncSession = Depends(get_db),
        user: UserModel = Depends(get_current_user)
):
    """
    Мягкое удаление отзыва
    """
    review = (await db.scalars(
        select(ReviewModel).where(
            ReviewModel.id == review_id, ReviewModel.is_active == True
        )
    )).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Review with this id not found'
        )
    if review.user_id != user.id or user.role not in ['buyer', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You can`t create review'
        )
    review.is_active = False
    await db.commit()
    await update_grade_product(db, review.product_id)
    return {"message": "Review deleted"}
