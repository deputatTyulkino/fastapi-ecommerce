from decimal import Decimal
from typing import Any
from anyio import to_thread  # Для запуска синхронного кода в async (FastAPI)
from yookassa import Configuration, Payment
from uuid import uuid4
from app.config import YOOKASSA_RETURN_URL, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY


async def create_yookassa_payment(
        *,
        order_id: int,
        amount: Decimal,
        user_email: str,
        description: str
) -> dict[str, Any]:
    # 1. Проверка настроек (fallback на ошибку)
    if not YOOKASSA_SECRET_KEY or not YOOKASSA_SHOP_ID:
        raise RuntimeError('Задайте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env')

    # 2. Глобальная настройка SDK (Basic Auth под капотом)
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY

    # 3. ФОРМИРОВАНИЕ PAYLOAD — ГЛАВНАЯ ЧАСТЬ!
    # Это JSON для POST /v3/payments.
    payload = {
        'amount': {  # Сумма платежа
            'value': f'{amount:.2f}',
            'currency': 'RUB'
        },
        'confirmation': {  # Как подтвердить платеж
            'type': 'redirect',  # Пользователь редиректится на форму YooKassa
            'return_url': YOOKASSA_RETURN_URL
        },
        'capture': True,  # Авто-списание денег после авторизации
        'description': description,  # Видно пользователю в истории
        'metadata': {  # Ваши данные (сохраняются в платеже)
            'order_id': order_id  # Связь с заказом из БД
        },
        'receipt': {  # ФИСКальный ЧЕК (обязателен по 54-ФЗ для РФ!)
            'customer': {  # Данные плательщика
                'email': user_email  # Чек придет на email
            },
            'items': [
                # Список "товаров"/услуг (здесь 1 item = весь наш заказ)
                # Но также мы можем передать и каждую позицию отдельно.
                {
                    "description": description[:128],  # Макс. 128 символов!
                    "quantity": "1.00",  # Кол-во (строка)
                    "amount": {  # Сумма item
                        "value": f"{amount:.2f}",
                        "currency": "RUB",
                    },
                    "vat_code": 1,  # НДС: 1=без НДС (0%), 2=0%, 3=10%, 4=20%, 5=расчетный, 6=спецрежим
                    "payment_mode": "full_prepayment",  # Режим: полная предоплата
                    "payment_subject": "commodity",  # Тип: "service"=услуга, "commodity"=товар или заказ
                },
            ]
        }
    }

    # 4. Вспомогательная синхронная функция для создания платежа
    def _request() -> Payment:
        # Payment.create(payload, idempotence_key) — POST запрос к API YooKassa
        # uuid4(): уникальный ключ, если повтор — вернет существующий платеж (идепотентность!)
        return Payment.create(payload, str(uuid4()))

    # 5. Вызов в thread (библиотека YooKassa синхронная, а FastAPI ассинхронный)
    payment: Payment = await to_thread.run_sync(_request)

    # 6. Извлечение URL для оплаты
    confirmation_url = getattr(payment.confirmation, 'confirmation_url', None)

    # 7. Возврат данных для фронта/БД
    return {
        "id": payment.id,
        # ID платежа, полученного от YooKassa
        "status": payment.status,
        # Статус платежа, пока он будет "pending"
        "confirmation_url": confirmation_url,
        # Ссылка на оплату(именно сюда перенаправит пользователя для оплаты)
    }
