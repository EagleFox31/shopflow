from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/shops/{shop_id}/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
def list_categories(shop_id: int, session: Session = Depends(get_db)):
    return category_service.list_categories(shop_id, session)


@router.post("/", response_model=CategoryRead, status_code=201)
def create_category(
    shop_id: int,
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return category_service.create_category(shop_id, current_user.id, data, session)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    shop_id: int,
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return category_service.update_category(
        shop_id, category_id, current_user.id, data, session
    )


@router.delete("/{category_id}", status_code=204)
def delete_category(
    shop_id: int,
    category_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    category_service.delete_category(shop_id, category_id, current_user.id, session)
    return Response(status_code=204)
