# Promotion API Guide

Complete documentation for the Promotion API endpoints in MobilePoint Backend.

## Base URL
```
/api/promotions/
```

## Overview

The Promotion API manages promotional offers including:
- **Free Shipping**: Promotions offering free shipping
- **Free Gift**: Promotions offering free gifts

### Key Features
- Time-based active status (automatic activation/expiration)
- Product association (multiple products per promotion)
- Advanced filtering and search
- Statistics and summary endpoints
- Pagination support

---

## Standard CRUD Endpoints

### 1. List All Promotions
Retrieve all promotions with optional filtering and pagination.

**Endpoint:** `GET /api/promotions/`

**Query Parameters:**
| Parameter | Type | Description | Example |
|---|---|---|---|
| `promotion_type` | string | Filter by type | `free_shipping` or `free_gift` |
| `is_active` | boolean | Filter by active status | `true` or `false` |
| `search` | string | Search in title/description | `"free shipping"` |
| `ordering` | string | Order results | `start_date`, `-created_at` |
| `limit` | integer | Results per page | `20` |
| `offset` | integer | Pagination offset | `0` |

**Response:**
```json
{
  "count": 10,
  "next": "http://api.example.com/promotions/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "promotion_type": "free_shipping",
      "title": "Free Shipping on Orders Over $50",
      "description": "Get free shipping when you spend $50 or more",
      "start_date": "2024-02-01T00:00:00Z",
      "end_date": "2024-02-28T23:59:59Z",
      "is_active": true,
      "is_currently_active": true,
      "product_count": 5,
      "remaining_days": 4,
      "created_at": "2024-01-25T10:30:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Authentication required for some filters

---

### 2. Get Promotion Details
Retrieve detailed information about a specific promotion including all associated products.

**Endpoint:** `GET /api/promotions/{id}/`

**Path Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Promotion ID |

**Response:**
```json
{
  "id": 1,
  "promotion_type": "free_shipping",
  "title": "Free Shipping on Orders Over $50",
  "description": "Get free shipping when you spend $50 or more",
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-28T23:59:59Z",
  "is_active": true,
  "is_currently_active": true,
  "product_count": 5,
  "remaining_days": 4,
  "products": [
    {
      "id": 1,
      "name": "iPhone 15 Pro",
      "slug": "iphone-15-pro",
      "base_price": "999.99",
      "category": { "id": 1, "name": "Smartphones" }
    }
  ],
  "created_at": "2024-01-25T10:30:00Z",
  "updated_at": "2024-01-26T15:45:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Promotion not found

---

### 3. Create Promotion
Create a new promotion. **Admin only**.

**Endpoint:** `POST /api/promotions/`

**Request Body:**
```json
{
  "promotion_type": "free_shipping",
  "title": "Spring Sale - Free Shipping",
  "description": "Free shipping on all orders during spring sale",
  "start_date": "2024-03-01T00:00:00Z",
  "end_date": "2024-03-31T23:59:59Z",
  "is_active": true,
  "product_ids": [1, 2, 3, 5]
}
```

**Request Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `promotion_type` | string | Yes | `free_shipping` or `free_gift` |
| `title` | string | Yes | Promotion title (max 150 chars) |
| `description` | string | No | Detailed description |
| `start_date` | datetime | Yes | Start time (ISO 8601) |
| `end_date` | datetime | Yes | End time (must be after start_date) |
| `is_active` | boolean | No | Enable/disable (default: true) |
| `product_ids` | array | No | List of product IDs to associate |

**Response:**
```json
{
  "id": 10,
  "promotion_type": "free_shipping",
  "title": "Spring Sale - Free Shipping",
  "description": "Free shipping on all orders during spring sale",
  "start_date": "2024-03-01T00:00:00Z",
  "end_date": "2024-03-31T23:59:59Z",
  "is_active": true,
  "product_ids": [1, 2, 3, 5]
}
```

**Status Codes:**
- `201 Created` - Success
- `400 Bad Request` - Invalid data or validation error
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized (admin only)

**Validation Errors:**
```json
{
  "end_date": ["End date must be after start date."],
  "promotion_type": ["Invalid choice"]
}
```

---

### 4. Update Promotion
Update an existing promotion. **Admin only**.

**Endpoint:** `PUT /api/promotions/{id}/` or `PATCH /api/promotions/{id}/`

**Path Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Promotion ID |

**Request Body (same as Create):**
```json
{
  "title": "Updated Promotion Title",
  "end_date": "2024-04-15T23:59:59Z"
}
```

**Status Codes:**
- `200 OK` - Success (PUT or PATCH)
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Promotion not found

---

### 5. Delete Promotion
Delete a promotion. **Admin only**.

**Endpoint:** `DELETE /api/promotions/{id}/`

**Path Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Promotion ID |

**Status Codes:**
- `204 No Content` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Promotion not found

---

## Custom Action Endpoints

### 6. Get Active Promotions
Retrieve all currently active promotions (time-based).

**Endpoint:** `GET /api/promotions/active/`

A promotion is considered "active" if:
- `is_active = true`
- `start_date <= current_time`
- `end_date >= current_time`

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Results per page |
| `offset` | integer | Pagination offset |
| `ordering` | string | Order results |

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "promotion_type": "free_shipping",
      "title": "Active Promotion",
      "is_currently_active": true,
      "remaining_days": 5
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success

---

### 7. Get Promotions by Type
Filter promotions by type (free shipping or free gift).

**Endpoint:** `GET /api/promotions/by-type/?type=free_shipping`

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `type` | string | Yes | `free_shipping` or `free_gift` |
| `limit` | integer | No | Results per page |
| `offset` | integer | No | Pagination offset |

**Example Requests:**
```
GET /api/promotions/by-type/?type=free_shipping
GET /api/promotions/by-type/?type=free_gift&limit=10
```

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "promotion_type": "free_shipping",
      "title": "Free Shipping Promotion"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Missing 'type' parameter or invalid value

**Error Response:**
```json
{
  "error": "type query parameter is required (free_shipping or free_gift)"
}
```

---

### 8. Get Promotion Products
Retrieve all active products associated with a specific promotion.

**Endpoint:** `GET /api/promotions/{id}/products/`

**Path Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Promotion ID |

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Results per page |
| `offset` | integer | Pagination offset |

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "iPhone 15 Pro",
      "slug": "iphone-15-pro",
      "base_price": "999.99",
      "primary_image": "https://example.com/image.jpg",
      "category": { "id": 1, "name": "Smartphones" },
      "brand": { "id": 2, "name": "Apple" }
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Promotion not found

---

### 9. Get Upcoming Promotions
Retrieve promotions that haven't started yet.

**Endpoint:** `GET /api/promotions/upcoming/`

Returns promotions where:
- `is_active = true`
- `start_date > current_time`

Results are ordered by start_date (earliest first).

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Results per page |
| `offset` | integer | Pagination offset |

**Status Codes:**
- `200 OK` - Success

---

### 10. Get Expired Promotions
Retrieve promotions that have already ended.

**Endpoint:** `GET /api/promotions/expired/`

Returns promotions where:
- `end_date < current_time`

Results are ordered by end_date (most recent first).

**Status Codes:**
- `200 OK` - Success

---

### 11. Get Promotions Summary
Retrieve statistics and summary information about all promotions.

**Endpoint:** `GET /api/promotions/summary/`

**Response:**
```json
{
  "total_promotions": 15,
  "active_promotions": 5,
  "inactive_promotions": 3,
  "upcoming_promotions": 4,
  "expired_promotions": 3,
  "by_type": {
    "free_shipping": 8,
    "free_gift": 7
  }
}
```

**Status Codes:**
- `200 OK` - Success (not paginated)

---

## Authentication & Permissions

### Permission Levels
| Endpoint | Anonymous | Authenticated | Admin |
|---|---|---|---|
| List | ✅ | ✅ | ✅ |
| Retrieve | ✅ | ✅ | ✅ |
| Create | ❌ | ✅ | ✅ |
| Update | ❌ | ✅ | ✅ |
| Delete | ❌ | ✅ | ✅ |
| Custom Actions | ✅ | ✅ | ✅ |

### Authentication Methods
```
Authorization: Token YOUR_AUTH_TOKEN
```

---

## Filtering & Search Examples

### Filter by Type
```
GET /api/promotions/?promotion_type=free_shipping
GET /api/promotions/?promotion_type=free_gift
```

### Filter by Active Status
```
GET /api/promotions/?is_active=true
GET /api/promotions/?is_active=false
```

### Search
```
GET /api/promotions/?search=spring
GET /api/promotions/?search=shipping
```

### Combined Filtering
```
GET /api/promotions/?promotion_type=free_shipping&is_active=true&search=spring
```

### Ordering
```
GET /api/promotions/?ordering=-start_date
GET /api/promotions/?ordering=end_date
GET /api/promotions/?ordering=-created_at
```

---

## Pagination Examples

### Basic Pagination
```
GET /api/promotions/?limit=20&offset=0      # First 20 results
GET /api/promotions/?limit=20&offset=20     # Next 20 results
```

### With Filtering
```
GET /api/promotions/?promotion_type=free_shipping&limit=10&offset=0
```

---

## Date Format

All dates must be in **ISO 8601 format**:
- With timezone: `2024-02-01T00:00:00Z` or `2024-02-01T00:00:00+00:00`
- Without timezone: `2024-02-01T00:00:00`

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid promotion type",
  "details": "Choose from: free_shipping, free_gift"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**Validation Error:**
```json
{
  "end_date": ["End date must be after start date."],
  "title": ["This field is required."]
}
```

---

## Example Use Cases

### 1. Display Active Promotions on Homepage
```bash
curl "http://api.example.com/api/promotions/active/?limit=5"
```

### 2. Show All Free Shipping Offers
```bash
curl "http://api.example.com/api/promotions/by-type/?type=free_shipping"
```

### 3. Check Promotion Statistics
```bash
curl "http://api.example.com/api/promotions/summary/"
```

### 4. Get Products in a Promotion
```bash
curl "http://api.example.com/api/promotions/1/products/"
```

### 5. Create New Promotion (Admin)
```bash
curl -X POST "http://api.example.com/api/promotions/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "promotion_type": "free_shipping",
    "title": "Spring Sale",
    "description": "Free shipping on all orders",
    "start_date": "2024-03-01T00:00:00Z",
    "end_date": "2024-03-31T23:59:59Z",
    "is_active": true,
    "product_ids": [1, 2, 3]
  }'
```

---

## Swagger Documentation

Interactive API documentation is available at:
```
http://your-domain.com/api/schema/swagger/
http://your-domain.com/api/schema/redoc/
```

---

## Rate Limiting

No rate limiting is currently enforced. Contact support for production rate limiting requirements.

---

## Changelog

### Version 1.0.0 (2024-02-24)
- Initial release
- CRUD operations for promotions
- Time-based active status
- Product association
- Advanced filtering and search
- Statistics endpoint
