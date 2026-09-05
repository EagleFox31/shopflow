from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InvalidStateError, NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import category_service, shop_service


def get_product(
    shop_id: int,
    product_id: int,
    session: Session,
    *,
    for_update: bool = False,
) -> Product:
    statement = select(Product).where(
        Product.id == product_id,
        Product.shop_id == shop_id,
    )
    if for_update:
        statement = statement.with_for_update()
    product = session.scalar(statement)
    if not product:
        raise NotFoundError("Product not found")
    return product


def list_products(
    shop_id: int,
    session: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
) -> list[Product]:
    statement = select(Product).where(Product.shop_id == shop_id)
    if active_only:
        statement = statement.where(Product.is_active.is_(True))
    statement = statement.order_by(Product.id).offset(skip).limit(limit)
    return list(session.scalars(statement).all())


def create_product(
    shop_id: int,
    actor_id: int,
    data: ProductCreate,
    session: Session,
) -> Product:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    category_service.validate_category_rules(shop_id, data.category_id, session)
    duplicate = session.scalar(
        select(Product).where(Product.shop_id == shop_id, Product.sku == data.sku)
    )
    if duplicate:
        raise ConflictError("SKU already exists in this shop")
    product = Product(shop_id=shop_id, **data.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(
    shop_id: int,
    product_id: int,
    actor_id: int,
    data: ProductUpdate,
    session: Session,
) -> Product:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    product = get_product(shop_id, product_id, session)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        category_service.validate_category_rules(shop_id, changes["category_id"], session)
    new_sku = changes.get("sku")
    if new_sku is not None and new_sku != product.sku:
        duplicate = session.scalar(
            select(Product).where(
                Product.shop_id == shop_id,
                Product.sku == new_sku,
                Product.id != product.id,
            )
        )
        if duplicate:
            raise ConflictError("SKU already exists in this shop")
    for field, value in changes.items():
        setattr(product, field, value)
    session.commit()
    session.refresh(product)
    return product


def delete_product(
    shop_id: int,
    product_id: int,
    actor_id: int,
    session: Session,
) -> None:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    product = get_product(shop_id, product_id, session)
    product.is_active = False
    session.commit()


def check_availability(product: Product, quantity: int) -> None:
    if not product.is_active:
        raise InvalidStateError(f"Product {product.id} is inactive")
    if product.stock_quantity < quantity:
        raise InvalidStateError(f"Insufficient stock for product {product.id}")


def reserve_stock(product: Product, quantity: int, session: Session) -> None:
    check_availability(product, quantity)
    product.stock_quantity -= quantity
    session.flush()


def release_stock(product: Product, quantity: int, session: Session) -> None:
    product.stock_quantity += quantity
    session.flush()
