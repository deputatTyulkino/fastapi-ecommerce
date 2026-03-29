from pydantic import BaseModel, ConfigDict, Field


class Review(BaseModel):
    id: int
    user_id: int
    product_id: int
    comment: str
    comment_date: str
    grade: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class CreateReview(BaseModel):
    product_id: int
    comment: str | None
    grade: int = Field(..., ge=0, le=5)
