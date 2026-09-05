from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/shops/{shop_id}/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
def list_products(
    shop_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_db),
):
    return product_service.list_products(shop_id, session, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(shop_id: int, product_id: int, session: Session = Depends(get_db)):
    return product_service.get_product(shop_id, product_id, session)


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(
    shop_id: int,
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return product_service.create_product(shop_id, current_user.id, data, session)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    shop_id: int,
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return product_service.update_product(
        shop_id, product_id, current_user.id, data, session
    )


@router.delete("/{product_id}", status_code=204)
def delete_product(
    shop_id: int,
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    product_service.delete_product(shop_id, product_id, current_user.id, session)
    return Response(status_code=204)
