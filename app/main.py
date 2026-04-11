from fastapi import FastAPI

from app.routers import categories, products, users, reviews, cart_items

app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.reviews_router)
app.include_router(cart_items.router)


@app.get("/")
async def root() -> dict:
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API интернет-магазина!"}
