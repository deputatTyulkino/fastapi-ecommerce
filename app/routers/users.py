import jwt
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import SECRET_KEY, ALGORITHM
from app.db_depends import get_db
from app.schemas.users import User as UserSchema, UserCreate, RefreshTokenRequest
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
    refresh_token = create_refresh_token(
        data={'sub': user.email, 'role': user.role, 'id': user.id}
    )
    returned_user = {
        'id': user.id,
        'email': user.email,
        'role': user.role
    }
    return {
        'access_token': access_token, 'refresh_token': refresh_token, 'user': returned_user
    }


@router.post('/refresh-token')
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Обновляет refresh и access токены, принимая старый refresh-токен в теле запроса.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    old_refresh_token = body.refresh_token
    try:
        payload = jwt.decode(old_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get('sub')
        token_type: str | None = payload.get('token_type')
        if email is None or token_type != 'refresh':
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = (await db.scalars(
        select(UserModel).where(UserModel.email == email, UserModel.is_active == True)
    )).first()
    if user is None:
        raise credentials_exception
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )
    new_access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )
    return {
        'refresh_token': new_refresh_token,
        'access_token': new_access_token
    }
