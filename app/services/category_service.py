from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import shop_service


def get_category(shop_id: int, category_id: int, session: Session) -> Category:
    category = session.scalar(
        select(Category).where(Category.id == category_id, Category.shop_id == shop_id)
    )
    if not category:
        raise NotFoundError("Category not found")
    return category


def create_category(
    shop_id: int,
    actor_id: int,
    data: CategoryCreate,
    session: Session,
) -> Category:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    duplicate = session.scalar(
        select(Category).where(Category.shop_id == shop_id, Category.slug == data.slug)
    )
    if duplicate:
        raise ConflictError("Category slug already exists in this shop")
    category = Category(shop_id=shop_id, **data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_categories(shop_id: int, session: Session) -> list[Category]:
    return list(
        session.scalars(
            select(Category).where(Category.shop_id == shop_id).order_by(Category.name)
        ).all()
    )


def update_category(
    shop_id: int,
    category_id: int,
    actor_id: int,
    data: CategoryUpdate,
    session: Session,
) -> Category:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    category = get_category(shop_id, category_id, session)
    changes = data.model_dump(exclude_unset=True)
    new_slug = changes.get("slug")
    if new_slug is not None and new_slug != category.slug:
        duplicate = session.scalar(
            select(Category).where(
                Category.shop_id == shop_id,
                Category.slug == new_slug,
                Category.id != category.id,
            )
        )
        if duplicate:
            raise ConflictError("Category slug already exists in this shop")
    for field, value in changes.items():
        setattr(category, field, value)
    session.commit()
    session.refresh(category)
    return category


def delete_category(
    shop_id: int,
    category_id: int,
    actor_id: int,
    session: Session,
) -> None:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_catalog", session)
    category = get_category(shop_id, category_id, session)
    if session.scalar(select(Product.id).where(Product.category_id == category.id).limit(1)):
        raise ConflictError("Cannot delete a category that still contains products")
    session.delete(category)
    session.commit()


def validate_category_rules(shop_id: int, category_id: int | None, session: Session) -> None:
    if category_id is not None:
        get_category(shop_id, category_id, session)
