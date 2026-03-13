from fastapi import APIRouter

router = APIRouter(
    prefix='/categories',
    tags=['categories']
)


@router.get('/')
async def get_all_categories() -> dict:
    """
    Возвращает список всех категорий товаров.
    """
    return {"message": "List of all categories"}


@router.post('/')
async def create_category() -> dict:
    """
    Создаёт новую категорию.
    """
    return {"message": "Create new category"}


@router.put('/{category_id}')
async def update_category(category_id: int) -> dict:
    """
    Обновляет категорию по её ID.
    """
    return {"message": f"Category with ID: {category_id} updated"}


@router.delete('/{category_id}')
async def delete_category(category_id: int) -> dict:
    """
    Удаляет категорию по её ID.
    """
    return {"message": f"Category with ID: {category_id} deleted"}
