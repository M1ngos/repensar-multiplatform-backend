# app/models/blog.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BlogPostStatus(str, Enum):
    draft = "draft"
    published = "published"


class BlogPost(SQLModel, table=True):
    __tablename__ = "blog_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, index=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    content: str = Field(sa_column=Column(Text))
    excerpt: Optional[str] = Field(default=None, max_length=500)
    status: BlogPostStatus = Field(default=BlogPostStatus.draft, index=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    featured_image_url: Optional[str] = Field(default=None, max_length=500)
    published_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    categories: List["BlogPostCategory"] = Relationship(back_populates="blog_post")
    tags: List["BlogPostTag"] = Relationship(back_populates="blog_post")


class Category(SQLModel, table=True):
    __tablename__ = "blog_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    slug: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    blog_posts: List["BlogPostCategory"] = Relationship(back_populates="category")


class Tag(SQLModel, table=True):
    __tablename__ = "blog_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    slug: str = Field(max_length=50, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    blog_posts: List["BlogPostTag"] = Relationship(back_populates="tag")


class BlogPostCategory(SQLModel, table=True):
    __tablename__ = "blog_post_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_post_id: int = Field(foreign_key="blog_posts.id", index=True)
    category_id: int = Field(foreign_key="blog_categories.id", index=True)

    # Relationships
    blog_post: BlogPost = Relationship(back_populates="categories")
    category: Category = Relationship(back_populates="blog_posts")


class BlogPostTag(SQLModel, table=True):
    __tablename__ = "blog_post_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_post_id: int = Field(foreign_key="blog_posts.id", index=True)
    tag_id: int = Field(foreign_key="blog_tags.id", index=True)

    # Relationships
    blog_post: BlogPost = Relationship(back_populates="tags")
    tag: Tag = Relationship(back_populates="blog_posts")
