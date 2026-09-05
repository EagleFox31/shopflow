from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


def _get_owned_address(address_id: int, user_id: int, session: Session) -> Address:
    address = session.get(Address, address_id)
    if not address:
        raise NotFoundError("Address not found")
    if address.user_id != user_id:
        raise ForbiddenError("Address does not belong to this user")
    return address


def create_address(user_id: int, data: AddressCreate, session: Session) -> Address:
    if data.is_default:
        session.execute(
            update(Address).where(Address.user_id == user_id).values(is_default=False)
        )
    address = Address(user_id=user_id, **data.model_dump())
    session.add(address)
    session.commit()
    session.refresh(address)
    return address


def list_addresses(user_id: int, session: Session) -> list[Address]:
    return list(
        session.scalars(
            select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.id)
        ).all()
    )


def update_address(
    address_id: int,
    user_id: int,
    data: AddressUpdate,
    session: Session,
) -> Address:
    address = _get_owned_address(address_id, user_id, session)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("is_default") is True:
        session.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.id != address_id)
            .values(is_default=False)
        )
    for field, value in changes.items():
        setattr(address, field, value)
    session.commit()
    session.refresh(address)
    return address


def delete_address(address_id: int, user_id: int, session: Session) -> None:
    address = _get_owned_address(address_id, user_id, session)
    session.delete(address)
    session.commit()


def set_default_address(address_id: int, user_id: int, session: Session) -> Address:
    address = _get_owned_address(address_id, user_id, session)
    session.execute(
        update(Address).where(Address.user_id == user_id).values(is_default=False)
    )
    address.is_default = True
    session.commit()
    return address


def validate_order_address(address_id: int, user_id: int, session: Session) -> Address:
    return _get_owned_address(address_id, user_id, session)
