# Frontend API Map

## Base URLs

- Catalog and cart API: `/api/v1/`
- Auth API: `/api/auth/`

## Authentication

Protected endpoints expect:

```http
Authorization: Bearer <access_token>
```

## Auth Endpoints

### Login

- `POST /api/auth/login/`

Request:

```json
{
  "username": "pavel",
  "password": "StrongPass123"
}
```

Response:

```json
{
  "user": {
    "id": 1,
    "username": "pavel",
    "email": "pavel@example.com"
  },
  "refresh": "jwt-refresh-token",
  "access": "jwt-access-token"
}
```

### Register

- `POST /api/auth/register/`

Request:

```json
{
  "username": "pavel",
  "email": "pavel@example.com",
  "password": "StrongPass123",
  "password2": "StrongPass123",
  "first_name": "Pavel",
  "last_name": "Ivanov"
}
```

### Verify Email PIN

- `POST /api/auth/verify-email-pin/`

Request:

```json
{
  "email": "pavel@example.com",
  "pin": "123456"
}
```

### Resend Email PIN

- `POST /api/auth/resend-email-pin/`

### Logout

- `POST /api/auth/logout/`

### Profile

- `GET /api/auth/profile/`
- `PUT /api/auth/profile/`
- `PATCH /api/auth/profile/`

### Change Password

- `PUT /api/auth/change-password/`

Request:

```json
{
  "old_password": "OldPass123",
  "new_password": "NewPass123"
}
```

### JWT Utility Endpoints

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/custom-refresh/`

## Catalog Endpoints

### Categories

- `GET /api/v1/categories/`
- `GET /api/v1/categories/{slug}/`
- `GET /api/v1/categories/header-menu/`
- `GET /api/v1/categories/{slug}/products/`

Category object:

```json
{
  "id": 1,
  "name": "Смартфоны",
  "slug": "smartphones",
  "parent": null,
  "description": "",
  "image": null,
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-20T10:00:00Z"
}
```

### Brands

- `GET /api/v1/brands/`
- `GET /api/v1/brands/{slug}/`
- `GET /api/v1/brands/{slug}/products/`

### Products

- `GET /api/v1/products/`
- `GET /api/v1/products/{slug}/`
- `GET /api/v1/products/popular/`
- `GET /api/v1/products/search/?q=iphone`

`products` list and `search` return DRF paginated payload:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "iPhone 15 Pro",
      "slug": "iphone-15-pro",
      "brand": {
        "id": 1,
        "name": "Apple",
        "slug": "apple",
        "logo": null,
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:00:00Z"
      },
      "category": {
        "id": 1,
        "name": "Смартфоны",
        "slug": "smartphones",
        "parent": null,
        "description": "",
        "image": null,
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:00:00Z"
      },
      "short_description": "Флагманский смартфон Apple",
      "description": "Смартфон с титановым корпусом",
      "seo_title": "",
      "seo_description": "",
      "is_active": true,
      "is_preorder": false,
      "delivery_text": "",
      "warranty_months": 12,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-20T10:00:00Z",
      "images": [],
      "variants": [
        {
          "id": 1,
          "sku": "APL-IP15PRO-256",
          "attributes": {},
          "price": "999.00",
          "old_price": null,
          "is_active": true,
          "stock": 5
        }
      ]
    }
  ]
}
```

Search notes:

- Query param: `q`
- Search fields: `name`, `short_description`, `description`, `brand.name`, `category.name`, `variants.sku`
- Only active products are returned
- Empty `q` returns `400`

Error example:

```json
{
  "detail": "Query parameter \"q\" is required."
}
```

### Variants

- `GET /api/v1/variants/`
- `GET /api/v1/variants/{sku}/`

### Attributes

- `GET /api/v1/attributes/`
- `GET /api/v1/attributes/{slug}/`

### Overview

- `GET /api/v1/overview/`

Useful for homepage or one-shot catalog bootstrapping.

Response shape:

```json
{
  "brands": [],
  "categories": [],
  "catalog": [
    {
      "id": 1,
      "name": "Смартфоны",
      "slug": "smartphones",
      "products": []
    }
  ]
}
```

### Hero Blocks

- `GET /api/v1/hero-blocks/`
- `GET /api/v1/hero-blocks/{id}/`

For unauthenticated users only published and active hero blocks are returned.

## Cart Endpoints

Cart works for both authenticated users and guests. For guests it is bound to the current session.

### Get Cart

- `GET /api/v1/cart/`

Response shape:

```json
{
  "id": 1,
  "status": "active",
  "items": [
    {
      "id": 10,
      "variant": 1,
      "variant_name": "iPhone 15 Pro",
      "variant_attributes": {
        "color": "Black",
        "storage": "256GB"
      },
      "variant_price": "999.00",
      "variant_image": "/media/products/images/2026/02/06/iphone15-main.png",
      "quantity": 2,
      "total_price": "1998.00",
      "added_at": "2026-03-20T10:00:00Z"
    }
  ],
  "total_items": 2,
  "total_price": "1998.00",
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-20T10:00:00Z"
}
```

### Add Item

- `POST /api/v1/cart/add_item/`

Request:

```json
{
  "variant_id": 1,
  "quantity": 2
}
```

### Update Item

- `POST /api/v1/cart/update_item/`

Request:

```json
{
  "item_id": 10,
  "quantity": 3
}
```

### Remove Item

- `DELETE /api/v1/cart/remove_item/`

Request:

```json
{
  "item_id": 10
}
```

### Clear Cart

- `DELETE /api/v1/cart/clear/`

### Checkout

- `POST /api/v1/cart/checkout/`

Current response is a placeholder:

```json
{
  "cart": {},
  "message": "Переход к оформлению заказа",
  "next_step": "/checkout"
}
```

## Orders

These endpoints require authentication.

- `GET /api/v1/orders/`
- `POST /api/v1/orders/`
- `GET /api/v1/orders/{id}/`
- `PUT /api/v1/orders/{id}/`
- `PATCH /api/v1/orders/{id}/`
- `DELETE /api/v1/orders/{id}/`

## Frontend Notes

- Product detail route should use `slug`
- Brand route should use `slug`
- Category route should use `slug`
- Attribute route should use `slug`
- Variant detail route should use `sku`
- Product list endpoints are paginated
- Category, brand and related product endpoints currently return full arrays without pagination
- `overview` is the simplest endpoint for initial catalog preload

## Known Caveat

`/api/v1/orders/` likely needs additional backend cleanup before frontend integration. The current order serializer does not fully match the visible order model fields.
