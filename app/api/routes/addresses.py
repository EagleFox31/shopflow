from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressRead])
def list_addresses(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return address_service.list_addresses(current_user.id, session)


@router.post("/", response_model=AddressRead, status_code=201)
def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return address_service.create_address(current_user.id, data, session)


@router.patch("/{address_id}", response_model=AddressRead)
def update_address(
    address_id: int,
    data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return address_service.update_address(address_id, current_user.id, data, session)


@router.post("/{address_id}/default", response_model=AddressRead)
def set_default(
    address_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return address_service.set_default_address(address_id, current_user.id, session)


@router.delete("/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    address_service.delete_address(address_id, current_user.id, session)
    return Response(status_code=204)
