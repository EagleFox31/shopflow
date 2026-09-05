from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.shop import (
    ShopAdminCreate,
    ShopAdminRead,
    ShopCreate,
    ShopRead,
    ShopUpdate,
)
from app.services import shop_admin_service, shop_service

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("/", response_model=list[ShopRead])
def my_shops(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_service.list_user_shops(current_user.id, session)


@router.post("/", response_model=ShopRead, status_code=201)
def create_shop(
    data: ShopCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_service.create_shop(current_user.id, data, session)


@router.get("/{shop_id}", response_model=ShopRead)
def get_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_service.assert_shop_access(shop_id, current_user.id, session)


@router.patch("/{shop_id}", response_model=ShopRead)
def update_shop(
    shop_id: int,
    data: ShopUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_service.update_shop(shop_id, current_user.id, data, session)


@router.post("/{shop_id}/close", response_model=ShopRead)
def close_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_service.close_shop(shop_id, current_user.id, session)


@router.get("/{shop_id}/admins", response_model=list[ShopAdminRead])
def list_admins(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_admin_service.list_admins(shop_id, current_user.id, session)


@router.post("/{shop_id}/admins", response_model=ShopAdminRead, status_code=201)
def add_admin(
    shop_id: int,
    data: ShopAdminCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return shop_admin_service.add_admin(shop_id, current_user.id, data, session)


@router.delete("/{shop_id}/admins/{user_id}", status_code=204)
def remove_admin(
    shop_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    shop_admin_service.remove_admin(shop_id, current_user.id, user_id, session)
    return Response(status_code=204)
