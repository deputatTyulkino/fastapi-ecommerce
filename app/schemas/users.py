from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr = Field(description='Email пользователя')
    password: str = Field(min_length=8, description='Пароль')
    role: str = Field(default='buyer', pattern='^(buyer|seller)$', description='Роль')


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
