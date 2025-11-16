# app/schemas/blog.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BlogPostStatus(str, Enum):
    draft = "draft"
    published = "published"


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class Category(CategoryBase):
    id: int
    slug: str
    created_at: datetime
    post_count: int = 0

    class Config:
        from_attributes = True


# Tag Schemas
class TagBase(BaseModel):
    name: str = Field(..., max_length=50)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class Tag(TagBase):
    id: int
    slug: str
    created_at: datetime
    post_count: int = 0

    class Config:
        from_attributes = True


# Author Schema (lightweight user info)
class Author(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


# Blog Post Schemas
class BlogPostBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    excerpt: Optional[str] = Field(None, max_length=500)
    status: BlogPostStatus = BlogPostStatus.draft
    featured_image_url: Optional[str] = Field(None, max_length=500)


class BlogPostCreate(BlogPostBase):
    category_ids: List[int] = []
    tag_ids: List[int] = []

    @field_validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        return v


class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=500)
    status: Optional[BlogPostStatus] = None
    featured_image_url: Optional[str] = Field(None, max_length=500)
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

    @field_validator('title')
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('content')
    def validate_content(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        return v


class BlogPost(BlogPostBase):
    id: int
    slug: str
    author_id: int
    author: Optional[Author] = None
    categories: List[Category] = []
    tags: List[Tag] = []
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlogPostSummary(BaseModel):
    """Lightweight blog post for list views"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    status: BlogPostStatus
    author_id: int
    author_name: Optional[str] = None
    featured_image_url: Optional[str]
    categories: List[Category] = []
    tags: List[Tag] = []
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlogPostListResponse(BaseModel):
    """Paginated list of blog posts"""
    items: List[BlogPostSummary]
    total: int
    skip: int
    limit: int


class CategoryListResponse(BaseModel):
    """Paginated list of categories"""
    items: List[Category]
    total: int
    skip: int
    limit: int


class TagListResponse(BaseModel):
    """Paginated list of tags"""
    items: List[Tag]
    total: int
    skip: int
    limit: int
