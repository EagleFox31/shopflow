# ShopFlow API Contracts

Base path: `/api/v1`

FastAPI generates the executable OpenAPI contract from these same Pydantic schemas. This document is the readable map of the main contracts.

## Authentication

### `POST /auth/register`

Request:

```json
{
  "email": "owner@example.com",
  "full_name": "Shop Owner",
  "password": "strong-password"
}
```

Returns `UserRead`.

### `POST /auth/login`

OAuth2 form fields: `username` (email) and `password`.

Returns:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### `POST /auth/refresh`

Request: `RefreshTokenRequest`. Returns a new `TokenPair`.

## Users and addresses

- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/change-password`
- `GET /addresses/`
- `POST /addresses/`
- `PATCH /addresses/{address_id}`
- `POST /addresses/{address_id}/default`
- `DELETE /addresses/{address_id}`

Addresses belong to the authenticated user and are validated again when an order is created.

## Shops

- `GET /shops/` — shops owned or administered by the current user
- `POST /shops/` — create another shop
- `GET /shops/{shop_id}`
- `PATCH /shops/{shop_id}` — owner only
- `POST /shops/{shop_id}/close` — owner only
- `GET /shops/{shop_id}/admins`
- `POST /shops/{shop_id}/admins`
- `DELETE /shops/{shop_id}/admins/{user_id}`

`ShopAdminCreate` contains per-shop permissions:

```json
{
  "user_id": 42,
  "can_manage_catalog": true,
  "can_manage_orders": true,
  "can_manage_users": false
}
```

## Catalog

### Categories

- `GET /shops/{shop_id}/categories/`
- `POST /shops/{shop_id}/categories/`
- `PATCH /shops/{shop_id}/categories/{category_id}`
- `DELETE /shops/{shop_id}/categories/{category_id}`

### Products

- `GET /shops/{shop_id}/products/`
- `GET /shops/{shop_id}/products/{product_id}`
- `POST /shops/{shop_id}/products/`
- `PATCH /shops/{shop_id}/products/{product_id}`
- `DELETE /shops/{shop_id}/products/{product_id}`

Example `ProductCreate`:

```json
{
  "category_id": 3,
  "name": "Wireless Keyboard",
  "sku": "KEY-001",
  "description": "Compact mechanical keyboard",
  "price": "25000.00",
  "stock_quantity": 12,
  "is_active": true
}
```

The pair `(shop_id, sku)` is unique.

## Cart

Each user has at most one `ACTIVE` cart **per shop**. The rule is enforced both in the service layer and by a partial unique database index.

- `GET /shops/{shop_id}/cart/`
- `PUT /shops/{shop_id}/cart/items`
- `DELETE /shops/{shop_id}/cart/items/{product_id}`
- `DELETE /shops/{shop_id}/cart/`

`PUT .../cart/items` is an upsert:

```json
{
  "product_id": 15,
  "quantity": 2
}
```

The service validates product availability and recalculates the cart total.

## Orders

### Customer flow

- `POST /shops/{shop_id}/orders` — create from the active cart
- `GET /orders/mine`
- `GET /orders/{order_id}`
- `PATCH /orders/{order_id}` — editable only before confirmation
- `POST /orders/{order_id}/cancel`
- `POST /orders/{order_id}/return`
- `GET /orders/{order_id}/history`

Create order:

```json
{
  "address_id": 7
}
```

### Shop-management flow

- `GET /shops/{shop_id}/orders?status=CONFIRMED`
- `POST /orders/{order_id}/confirm`
- `POST /orders/{order_id}/ship`
- `POST /orders/{order_id}/deliver`

Ship request:

```json
{
  "carrier": "DHL",
  "tracking_number": "DHL-123456"
}
```

### Lifecycle

```text
PENDING → PAID → CONFIRMED → SHIPPED → DELIVERED
   │                                      │
   └──────────────→ CANCELLED             └→ RETURNED
```

Clients never directly patch the `status` field. Status changes only through lifecycle endpoints.

## Payments

- `POST /orders/{order_id}/payments/`
- `POST /orders/{order_id}/payments/{payment_id}/success`
- `POST /orders/{order_id}/payments/{payment_id}/failure`

Payment providers are intentionally abstracted. A customer may initiate a payment, but payment success/failure cannot be self-declared by that customer: the current manual-provider endpoints require shop order-management permission. A real provider webhook can later replace that boundary without moving payment logic into routers.

## Platform roles

Global roles are separate from shop administration.

- `GET /admin/roles`
- `POST /admin/roles`
- `POST /admin/users/{user_id}/roles`
- `DELETE /admin/users/{user_id}/roles/{role_id}`

These endpoints require the `platform_admin` global role.

## Error contract

Domain errors share a consistent response shape:

```json
{
  "detail": "Human-readable domain error"
}
```

Typical status codes:

- `401` invalid credentials/token
- `403` missing shop/role permission
- `404` resource not found
- `409` uniqueness/domain conflict
- `422` invalid state transition or business rule
