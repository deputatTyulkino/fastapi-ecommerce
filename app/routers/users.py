from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_password, create_access_token
from app.db_depends import get_db
from app.schemas.users import User as UserSchema, UserCreate
from sqlalchemy import select
from app.models.users import User as UserModel

router = APIRouter(prefix='/auth', tags=['users'])


@router.post('/register', response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """

    # Переделать проверку на role = (buyer or seller) в схеме pydantic
    user_stmt = await db.scalars(select(UserModel).where(UserModel.email == user.email))
    if user_stmt.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    db_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    return db_user


@router.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Аутентифицирует пользователя и возвращает JWT с email, role и id.
    """
    result = await db.scalars(
        select(UserModel)
        .where(UserModel.email == form_data.username, UserModel.is_active == True)
    )
    user = result.first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={'sub': user.email, 'role': user.role, 'id': user.id}
    )
    returned_user = {
        'id': user.id,
        'email': user.email,
        'role': user.role
    }
    return {'access_token': access_token, 'user': returned_user}
