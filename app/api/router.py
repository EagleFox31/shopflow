from fastapi import APIRouter

from app.api.routes import (
    addresses,
    auth,
    cart,
    categories,
    orders,
    payments,
    products,
    roles,
    shops,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(addresses.router)
api_router.include_router(shops.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(roles.router)
