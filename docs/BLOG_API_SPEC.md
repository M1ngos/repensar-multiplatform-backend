# Blog API Specification

## Overview

The Blog module provides functionality for creating and managing blog posts with categories and tags. It includes draft/publish workflows and supports filtering and searching.

## Permissions

- **Create Posts**: Admin users only
- **Edit/Delete Posts**: Admin users only (post authors)
- **Publish Posts**: Admin users only
- **View Published Posts**: All users (including unauthenticated)
- **View Draft Posts**: Admin users only (post authors)
- **Manage Categories/Tags**: Admin users only

## Models

### BlogPost

```json
{
  "id": 1,
  "title": "Introduction to Environmental Conservation",
  "slug": "introduction-to-environmental-conservation",
  "content": "Full blog post content in markdown or HTML...",
  "excerpt": "A brief introduction to our conservation efforts...",
  "status": "published",
  "author_id": 1,
  "author": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com"
  },
  "featured_image_url": "https://example.com/images/post1.jpg",
  "categories": [
    {
      "id": 1,
      "name": "Conservation",
      "slug": "conservation"
    }
  ],
  "tags": [
    {
      "id": 1,
      "name": "Environment",
      "slug": "environment"
    },
    {
      "id": 2,
      "name": "Wildlife",
      "slug": "wildlife"
    }
  ],
  "published_at": "2025-01-15T10:00:00Z",
  "created_at": "2025-01-10T08:30:00Z",
  "updated_at": "2025-01-15T09:45:00Z"
}
```

### Category

```json
{
  "id": 1,
  "name": "Conservation",
  "slug": "conservation",
  "description": "Posts about conservation efforts and initiatives",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Tag

```json
{
  "id": 1,
  "name": "Environment",
  "slug": "environment",
  "created_at": "2025-01-01T00:00:00Z"
}
```

## Endpoints

### Blog Posts

#### List Blog Posts

```
GET /api/v1/blog/posts
```

**Query Parameters:**
- `status` (optional): Filter by status (`draft` or `published`). Default: `published` for non-admins, all for admins
- `category` (optional): Filter by category slug
- `tag` (optional): Filter by tag slug
- `search` (optional): Search in title, excerpt, and content
- `author_id` (optional): Filter by author ID
- `skip` (optional): Number of posts to skip. Default: 0
- `limit` (optional): Maximum number of posts to return. Default: 10, Max: 100

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Introduction to Environmental Conservation",
      "slug": "introduction-to-environmental-conservation",
      "excerpt": "A brief introduction...",
      "status": "published",
      "author": {
        "id": 1,
        "full_name": "John Doe"
      },
      "featured_image_url": "https://example.com/images/post1.jpg",
      "categories": [...],
      "tags": [...],
      "published_at": "2025-01-15T10:00:00Z",
      "created_at": "2025-01-10T08:30:00Z",
      "updated_at": "2025-01-15T09:45:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 10
}
```

#### Get Single Blog Post

```
GET /api/v1/blog/posts/{post_id}
```

or

```
GET /api/v1/blog/posts/by-slug/{slug}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "title": "Introduction to Environmental Conservation",
  "slug": "introduction-to-environmental-conservation",
  "content": "Full blog post content...",
  "excerpt": "A brief introduction...",
  "status": "published",
  "author": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com"
  },
  "featured_image_url": "https://example.com/images/post1.jpg",
  "categories": [...],
  "tags": [...],
  "published_at": "2025-01-15T10:00:00Z",
  "created_at": "2025-01-10T08:30:00Z",
  "updated_at": "2025-01-15T09:45:00Z"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Blog post not found"
}
```

#### Create Blog Post

```
POST /api/v1/blog/posts
```

**Authentication**: Required (Admin only)

**Request Body:**
```json
{
  "title": "New Blog Post",
  "content": "Full blog post content...",
  "excerpt": "A brief introduction...",
  "status": "draft",
  "featured_image_url": "https://example.com/images/post.jpg",
  "category_ids": [1, 2],
  "tag_ids": [1, 3, 5]
}
```

**Response: 201 Created**
```json
{
  "id": 2,
  "title": "New Blog Post",
  "slug": "new-blog-post",
  "content": "Full blog post content...",
  "excerpt": "A brief introduction...",
  "status": "draft",
  "author_id": 1,
  "author": {...},
  "featured_image_url": "https://example.com/images/post.jpg",
  "categories": [...],
  "tags": [...],
  "published_at": null,
  "created_at": "2025-01-20T10:00:00Z",
  "updated_at": "2025-01-20T10:00:00Z"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "A post with this slug already exists"
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Only administrators can create blog posts"
}
```

#### Update Blog Post

```
PUT /api/v1/blog/posts/{post_id}
```

**Authentication**: Required (Admin only, post author)

**Request Body:**
```json
{
  "title": "Updated Blog Post Title",
  "content": "Updated content...",
  "excerpt": "Updated excerpt...",
  "status": "published",
  "featured_image_url": "https://example.com/images/updated.jpg",
  "category_ids": [1, 3],
  "tag_ids": [2, 4]
}
```

**Response: 200 OK**
```json
{
  "id": 2,
  "title": "Updated Blog Post Title",
  "slug": "updated-blog-post-title",
  "content": "Updated content...",
  "excerpt": "Updated excerpt...",
  "status": "published",
  "author_id": 1,
  "author": {...},
  "featured_image_url": "https://example.com/images/updated.jpg",
  "categories": [...],
  "tags": [...],
  "published_at": "2025-01-20T11:00:00Z",
  "created_at": "2025-01-20T10:00:00Z",
  "updated_at": "2025-01-20T11:00:00Z"
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "You can only edit your own blog posts"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Blog post not found"
}
```

#### Delete Blog Post

```
DELETE /api/v1/blog/posts/{post_id}
```

**Authentication**: Required (Admin only, post author)

**Response: 204 No Content**

**Response: 403 Forbidden**
```json
{
  "detail": "You can only delete your own blog posts"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Blog post not found"
}
```

#### Publish Blog Post

```
POST /api/v1/blog/posts/{post_id}/publish
```

**Authentication**: Required (Admin only, post author)

**Response: 200 OK**
```json
{
  "id": 2,
  "title": "New Blog Post",
  "slug": "new-blog-post",
  "status": "published",
  "published_at": "2025-01-20T12:00:00Z",
  ...
}
```

#### Unpublish Blog Post (Revert to Draft)

```
POST /api/v1/blog/posts/{post_id}/unpublish
```

**Authentication**: Required (Admin only, post author)

**Response: 200 OK**
```json
{
  "id": 2,
  "title": "New Blog Post",
  "slug": "new-blog-post",
  "status": "draft",
  "published_at": null,
  ...
}
```

### Categories

#### List Categories

```
GET /api/v1/blog/categories
```

**Query Parameters:**
- `skip` (optional): Number of categories to skip. Default: 0
- `limit` (optional): Maximum number of categories to return. Default: 50

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Conservation",
      "slug": "conservation",
      "description": "Posts about conservation efforts",
      "post_count": 12,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

#### Get Single Category

```
GET /api/v1/blog/categories/{category_id}
```

or

```
GET /api/v1/blog/categories/by-slug/{slug}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "Conservation",
  "slug": "conservation",
  "description": "Posts about conservation efforts",
  "post_count": 12,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### Create Category

```
POST /api/v1/blog/categories
```

**Authentication**: Required (Admin only)

**Request Body:**
```json
{
  "name": "Wildlife",
  "description": "Posts about wildlife protection"
}
```

**Response: 201 Created**
```json
{
  "id": 2,
  "name": "Wildlife",
  "slug": "wildlife",
  "description": "Posts about wildlife protection",
  "post_count": 0,
  "created_at": "2025-01-20T10:00:00Z"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "A category with this name already exists"
}
```

#### Update Category

```
PUT /api/v1/blog/categories/{category_id}
```

**Authentication**: Required (Admin only)

**Request Body:**
```json
{
  "name": "Wildlife Protection",
  "description": "Updated description"
}
```

**Response: 200 OK**

#### Delete Category

```
DELETE /api/v1/blog/categories/{category_id}
```

**Authentication**: Required (Admin only)

**Response: 204 No Content**

**Response: 400 Bad Request**
```json
{
  "detail": "Cannot delete category that has associated blog posts"
}
```

### Tags

#### List Tags

```
GET /api/v1/blog/tags
```

**Query Parameters:**
- `skip` (optional): Number of tags to skip. Default: 0
- `limit` (optional): Maximum number of tags to return. Default: 100

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Environment",
      "slug": "environment",
      "post_count": 25,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 100
}
```

#### Get Single Tag

```
GET /api/v1/blog/tags/{tag_id}
```

or

```
GET /api/v1/blog/tags/by-slug/{slug}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "Environment",
  "slug": "environment",
  "post_count": 25,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### Create Tag

```
POST /api/v1/blog/tags
```

**Authentication**: Required (Admin only)

**Request Body:**
```json
{
  "name": "Climate Change"
}
```

**Response: 201 Created**
```json
{
  "id": 2,
  "name": "Climate Change",
  "slug": "climate-change",
  "post_count": 0,
  "created_at": "2025-01-20T10:00:00Z"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "A tag with this name already exists"
}
```

#### Update Tag

```
PUT /api/v1/blog/tags/{tag_id}
```

**Authentication**: Required (Admin only)

**Request Body:**
```json
{
  "name": "Climate Action"
}
```

**Response: 200 OK**

#### Delete Tag

```
DELETE /api/v1/blog/tags/{tag_id}
```

**Authentication**: Required (Admin only)

**Response: 204 No Content**

## Error Responses

All endpoints may return the following error responses:

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**
```json
{
  "detail": "Insufficient permissions"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## Slug Generation

Slugs are automatically generated from titles/names:
- Converted to lowercase
- Spaces replaced with hyphens
- Special characters removed
- If duplicate, append `-{number}` (e.g., `post-title-2`)

## Notes

- All timestamps are in UTC ISO 8601 format
- When a post status changes from `draft` to `published`, `published_at` is set to the current timestamp
- When a post status changes from `published` to `draft`, `published_at` is set to `null`
- Non-admin users can only see published posts
- Admin users can see all posts (including drafts)
- Soft deletes can be implemented in the future if needed
- Full-text search will be implemented using PostgreSQL full-text search capabilities
